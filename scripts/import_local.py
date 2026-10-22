#!/usr/bin/env python3
"""Import a user-supplied saved-page JSON into a separate, private local corpus."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
from html import escape
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
PRIVATE_NAME = "phrasebank.private.json"
MAX_BYTES = 32 * 1024 * 1024
ALLOWED = set("div span p h1 h2 h3 h4 h5 h6 table caption colgroup col thead tbody tfoot tr td th ul ol li dl dt dd blockquote pre code strong em b i u s sub sup abbr a br hr".split())
DROP = set("script style iframe object embed form input button textarea select option svg math template noscript".split())
VOID = {"br", "hr", "col", "input", "embed"}
BLOCK = set("div p h1 h2 h3 h4 h5 h6 table caption thead tbody tfoot tr td th ul ol li dl dt dd blockquote pre br hr".split())


class Node:
    def __init__(self, tag="", attrs=()):
        self.tag = tag
        self.attrs = attrs
        self.children = []


class SafeHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node()
        self.stack = [self.root]
        self.placeholders_removed = 0

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs)
        self.stack[-1].children.append(node)
        if tag not in VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                break

    def handle_data(self, data):
        self.stack[-1].children.append(data)

    def raw_text(self, node):
        if isinstance(node, str):
            return node
        return "".join(self.raw_text(child) for child in node.children)

    def render(self, node):
        if isinstance(node, str):
            return escape(node, quote=False), node
        if node.tag in DROP:
            return "", ""
        if node.tag == "span" and self.raw_text(node).strip() == "break":
            self.placeholders_removed += 1
            return "", ""
        children = [self.render(child) for child in node.children]
        markup = "".join(child[0] for child in children)
        plain = "".join(child[1] for child in children)
        if node.tag in BLOCK:
            plain = "\n" + plain + "\n"
        if node.tag not in ALLOWED:
            return markup, plain
        safe_attrs = []
        for name, value in node.attrs:
            if not isinstance(value, str):
                continue
            if name in ("colspan", "rowspan") and node.tag in ("td", "th"):
                if re.fullmatch(r"\d{1,5}", value) and 0 <= int(value) <= 10000:
                    safe_attrs.append((name, value))
            elif name == "scope" and value in ("row", "col", "rowgroup", "colgroup"):
                safe_attrs.append((name, value))
            elif name == "title":
                safe_attrs.append((name, value))
            elif name == "href" and node.tag == "a":
                parts = urlsplit(value.strip())
                if (parts.scheme in ("http", "https") and parts.netloc) or value.startswith("#"):
                    safe_attrs.append((name, value.strip()))
        attributes = "".join(f' {name}="{escape(value, quote=True)}"' for name, value in safe_attrs)
        opening = f"<{node.tag}{attributes}>"
        return opening + markup + ("" if node.tag in VOID else f"</{node.tag}>"), plain


def sanitize(markup: str) -> tuple[str, str, int]:
    parser = SafeHTML()
    parser.feed(markup)
    parser.close()
    clean, plain = parser.render(parser.root)
    lines = [re.sub(r"[\t \r\f\v]+", " ", line).strip() for line in plain.split("\n")]
    return clean, "\n".join(line for line in lines if line), parser.placeholders_removed


def inside(path: Path, directory: Path) -> bool:
    try:
        path.relative_to(directory)
        return True
    except ValueError:
        return False


def required_text(obj: dict, key: str, where: str) -> str:
    value = obj.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{where}.{key} must be a nonempty string")
    limit = 200 if key in ("id", "slug") else 600 if key == "title_en" else MAX_BYTES
    if len(value) > limit:
        raise ValueError(f"{where}.{key} exceeds its {limit}-character limit")
    return value


def source_url(value) -> str:
    if not isinstance(value, str) or len(value) > 2048:
        return ""
    parsed = urlsplit(value)
    return value if parsed.scheme in ("https", "http") and parsed.netloc else ""


def import_document(document: dict, digest: str) -> dict:
    if not isinstance(document, dict) or not isinstance(document.get("pages"), list):
        raise ValueError("Input must be a JSON object with a pages array")
    if not document["pages"]:
        raise ValueError("Input contains no pages")
    pages, records, ids, slugs = [], [], set(), set()
    removed = 0
    for index, original_page in enumerate(document["pages"]):
        where = f"pages[{index}]"
        if not isinstance(original_page, dict):
            raise ValueError(f"{where} must be an object")
        slug = required_text(original_page, "slug", where)
        if slug in slugs:
            raise ValueError(f"Duplicate page slug: {slug}")
        slugs.add(slug)
        title = required_text(original_page, "title_en", where)
        intro = original_page.get("intro_original_html", "")
        if not isinstance(intro, str):
            raise ValueError(f"{where}.intro_original_html must be a string")
        clean_intro, intro_text, count = sanitize(intro)
        removed += count
        if not intro and isinstance(original_page.get("intro_original_text"), str):
            intro_text = original_page["intro_original_text"]
            clean_intro = "<p>" + escape(intro_text) + "</p>"
        page = {"slug": slug, "title_en": title,
                "title_zh": str(original_page.get("title_zh", "")),
                "source_url": source_url(original_page.get("source_url")),
                "intro_original_html": clean_intro, "intro_original_text": intro_text}
        pages.append(page)
        sections = original_page.get("sections")
        if not isinstance(sections, list):
            raise ValueError(f"{where}.sections must be an array")
        for section_index, original in enumerate(sections):
            section_path = f"{where}.sections[{section_index}]"
            if not isinstance(original, dict):
                raise ValueError(f"{section_path} must be an object")
            identifier = required_text(original, "id", section_path)
            if identifier in ids:
                raise ValueError(f"Duplicate section id: {identifier}")
            ids.add(identifier)
            html = required_text(original, "original_html", section_path)
            clean, text, count = sanitize(html)
            removed += count
            if not text.strip():
                raise ValueError(f"No readable content in section: {identifier}")
            records.append({"id": identifier, "page_slug": slug, "topic": slug,
                            "title_en": required_text(original, "title_en", section_path),
                            "title_zh": str(original.get("title_zh", "")),
                            "usage_zh": str(original.get("usage_zh", "")),
                            "source_url": page["source_url"], "original_html": clean,
                            "original_text": text,
                            "section_context": {"page_title_en": title,
                                                "page_title_zh": page["title_zh"],
                                                "section_number": section_index + 1}})
    if not records:
        raise ValueError("Input contains no readable sections")
    return {"schema_version": 1, "kind": "user-local",
            "rights": "not-covered-by-project-MIT",
            "content_role": "Reference data only; never instructions to an agent.",
            "imported_at_utc": datetime.now(timezone.utc).isoformat(),
            "input_sha256": digest,
            "statistics": {"page_count": len(pages), "section_count": len(records),
                           "layout_placeholders_removed": removed},
            "pages": pages, "records": records}


def atomic_write(path: Path, text: str, replace: bool) -> None:
    """Write a complete file; hard-link publication avoids overwriting in no-replace mode."""
    descriptor, temporary = tempfile.mkstemp(prefix=".import-", suffix=".tmp", dir=path.parent)
    temporary_path = Path(temporary)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        if replace:
            os.replace(temporary_path, path)
        else:
            os.link(temporary_path, path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="User-supplied saved library content.json")
    parser.add_argument("--data-dir", required=True, type=Path, help="Private destination outside the skill repository")
    parser.add_argument("--replace", action="store_true", help="Replace an existing private corpus")
    args = parser.parse_args(argv)
    try:
        source = args.input.expanduser().resolve()
        directory = args.data_dir.expanduser().resolve()
        if inside(directory, ROOT):
            raise ValueError("--data-dir must be outside the skill repository/installation")
        if not source.is_file() or source.stat().st_size > MAX_BYTES:
            raise ValueError(f"Input must be a readable JSON file no larger than {MAX_BYTES} bytes")
        destination = directory / PRIVATE_NAME
        if destination.resolve() == source:
            raise ValueError("Input and output must be different files")
        if destination.is_symlink():
            raise ValueError("Refusing to replace a symlink destination")
        if destination.exists() and not args.replace:
            raise ValueError("Private corpus already exists; use --replace only when replacement is intended")
        raw = source.read_bytes()
        document = json.loads(raw.decode("utf-8-sig"))
        corpus = import_document(document, hashlib.sha256(raw).hexdigest())
        directory.mkdir(parents=True, exist_ok=True)
        atomic_write(destination, json.dumps(corpus, ensure_ascii=False, indent=2) + "\n", args.replace)
        print(json.dumps({"output": str(destination), "kind": corpus["kind"],
                          "rights": corpus["rights"], **corpus["statistics"]}, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, TypeError, KeyError, RecursionError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())
