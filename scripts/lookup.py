#!/usr/bin/env python3
"""Offline, bounded retrieval of original coaching cards and optional local material."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
PRIVATE_NAME = "phrasebank.private.json"
MAX_FILE_BYTES = 32 * 1024 * 1024
MAX_GET_CHARS = 60000


def read_json(path: Path) -> dict:
    if path.stat().st_size > MAX_FILE_BYTES:
        raise ValueError(f"JSON exceeds {MAX_FILE_BYTES} bytes: {path.name}")
    with path.open(encoding="utf-8-sig") as stream:
        data = json.load(stream)
    if not isinstance(data, dict):
        raise ValueError(f"Expected a JSON object: {path.name}")
    return data


def local_directory(override: str | None) -> Path | None:
    value = override or os.environ.get("ACADEMIC_WRITING_COACH_DATA_DIR")
    if not value:
        config = ROOT / ".local-data-config.json"
        if config.exists():
            value = read_json(config).get("data_dir")
            if not isinstance(value, str) or not value.strip():
                raise ValueError("Local configuration needs a nonempty data_dir string")
    return Path(value).expanduser().resolve() if value else None


def load_records(dataset: str, directory: Path | None) -> tuple[list[dict], dict]:
    records: list[dict] = []
    status = {"builtin": {"available": False, "record_count": 0},
              "local": {"configured": directory is not None, "available": False,
                        "page_count": 0, "section_count": 0}}
    sources = []
    if dataset in ("builtin", "all"):
        sources.append(("builtin", ROOT / "references" / "moves.json"))
    local_file = directory / PRIVATE_NAME if directory else None
    if dataset in ("local", "all") and local_file and local_file.is_file():
        sources.append(("local", local_file))
    elif dataset == "local":
        raise ValueError("No local corpus found. Import one first or select --dataset builtin.")
    for provenance, path in sources:
        data = read_json(path)
        expected_kind = "original" if provenance == "builtin" else "user-local"
        if data.get("schema_version") != 1 or data.get("kind") != expected_kind:
            raise ValueError(f"Unsupported schema or kind in {path.name}")
        entries = data.get("records")
        if not isinstance(entries, list):
            raise ValueError(f"records must be an array in {path.name}")
        pages = {p["slug"]: p for p in data.get("pages", [])
                 if isinstance(p, dict) and isinstance(p.get("slug"), str)}
        seen = set()
        for entry in entries:
            if not isinstance(entry, dict) or not isinstance(entry.get("id"), str):
                raise ValueError(f"Every record needs a string id in {path.name}")
            if not 1 <= len(entry["id"]) <= 200:
                raise ValueError(f"Record ids must contain 1–200 characters in {path.name}")
            if entry["id"] in seen:
                raise ValueError(f"Duplicate record id in {path.name}: {entry['id']}")
            seen.add(entry["id"])
            record = dict(entry)
            record["provenance"] = provenance
            record["kind"] = expected_kind
            record["rights"] = "MIT" if provenance == "builtin" else "not-covered-by-project-MIT"
            if provenance == "local":
                record["page_context"] = pages.get(entry.get("page_slug"), {})
            records.append(record)
        status[provenance]["available"] = True
        if provenance == "builtin":
            status[provenance]["record_count"] = len(entries)
        else:
            status[provenance]["page_count"] = len(pages)
            status[provenance]["section_count"] = len(entries)
    return records, status


def terms(text: str) -> set[str]:
    text = text.casefold()
    output = set(re.findall(r"[a-z0-9]+", text))
    for run in re.findall(r"[\u3400-\u9fff]+", text):
        if len(run) == 1:
            output.add(run)
        else:
            output.update(run[i:i + 2] for i in range(len(run) - 1))
    return output


def flatten(value) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return " ".join(flatten(item) for item in value)
    return ""


def rank(record: dict, query: str) -> float:
    query_terms = terms(query)
    if not query_terms:
        return 0
    score = 0.0
    weights = {"id": 12, "title_en": 10, "title_zh": 10, "tags": 8,
               "topic": 7, "purpose_zh": 5, "usage_zh": 5,
               "when_to_use": 4, "steps": 2, "explanation_zh": 2,
               "original_text": 1, "example_before": 1, "example_after": 1}
    normalized_query = query.strip().casefold()
    for key, weight in weights.items():
        content = flatten(record.get(key)).casefold()
        overlap = len(query_terms.intersection(terms(content)))
        score += overlap * weight / len(query_terms)
        if normalized_query in content:
            score += 2 * weight
    return round(score, 4)


def excerpt(text: str, query: str, limit: int = 300) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    if len(compact) <= limit:
        return compact
    positions = [compact.casefold().find(term) for term in terms(query)]
    positions = [position for position in positions if position >= 0]
    start = max(0, min(positions) - 60) if positions else 0
    return ("…" if start else "") + compact[start:start + limit] + "…"


def summary(record: dict, query: str, score: float) -> dict:
    text = flatten(record.get("purpose_zh") or record.get("usage_zh") or record.get("original_text"))
    return {"id": record["id"], "provenance": record["provenance"],
            "rights": record["rights"], "score": score,
            "topic": record.get("topic", record.get("page_slug", "")),
            "title_en": str(record.get("title_en", ""))[:300],
            "title_zh": str(record.get("title_zh", ""))[:300],
            "excerpt": excerpt(text, query),
            "source_url": str(record.get("source_url", ""))[:2048],
            "section_context": {key: (str(value)[:300] if isinstance(value, str) else value)
                                for key, value in record.get("section_context", {}).items()
                                if key in ("page_title_en", "page_title_zh", "section_number")}}


def bounded_record(record: dict) -> dict:
    """Bound one response; retain full content in the local JSON on disk."""
    remaining = MAX_GET_CHARS
    truncated = []

    def visit(value, path):
        nonlocal remaining
        if isinstance(value, str):
            take = max(0, remaining)
            remaining -= min(len(value), take)
            if len(value) > take:
                truncated.append(path)
                return value[:take] + " [TRUNCATED; read the source JSON for the remainder]"
            return value
        if isinstance(value, list):
            return [visit(item, f"{path}[{index}]") for index, item in enumerate(value)]
        if isinstance(value, dict):
            return {key: visit(item, f"{path}.{key}") for key, item in value.items()}
        return value

    output = visit(record, "record")
    output["truncated_fields"] = truncated
    return output


def emit(payload, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    if isinstance(payload, dict) and "matches" in payload:
        print(f"{len(payload['matches'])} of {payload['match_count']} matching records")
        for item in payload["matches"]:
            print(f"\n[{item['provenance']}] {item['id']} — {item['title_en']} / {item['title_zh']}")
            print(item["excerpt"])
            if item["source_url"]:
                print(f"Source: {item['source_url']}")
        return
    if isinstance(payload, dict) and "id" in payload:
        print(f"[{payload['provenance']}] {payload['id']}")
        print(f"{payload.get('title_en', '')} / {payload.get('title_zh', '')}")
        print(f"Rights: {payload['rights']}")
        for key in ("purpose_zh", "when_to_use", "usage_zh", "steps", "example_before",
                    "example_after", "explanation_zh", "original_text", "source_url"):
            value = payload.get(key)
            if value:
                print(f"\n{key}:\n{flatten(value)}")
        if payload.get("page_context"):
            page = payload["page_context"]
            print(f"\nPage context: {page.get('title_en', '')}")
            print(page.get("intro_original_text", ""))
        if payload.get("truncated_fields"):
            print("\nSome fields were truncated; use --json to see field names or read the source JSON.")
        return
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    search = commands.add_parser("search", help="Rank matches in English and Chinese")
    search.add_argument("query")
    search.add_argument("--limit", type=int, default=5)
    search.add_argument("--dataset", choices=("builtin", "local", "all"), default="all")
    get = commands.add_parser("get", help="Read a complete card or local section by id")
    get.add_argument("id")
    status_parser = commands.add_parser("status", help="Report available data without revealing its contents")
    for command in (search, get, status_parser):
        command.add_argument("--data-dir", help="Directory containing phrasebank.private.json")
        command.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        directory = local_directory(args.data_dir)
        records, status = load_records(getattr(args, "dataset", "all"), directory)
        if args.command == "status":
            emit(status, args.json)
        elif args.command == "get":
            matches = [record for record in records if record["id"] == args.id]
            if not matches:
                raise ValueError(f"No record with id: {args.id}")
            if len(matches) != 1:
                raise ValueError(f"Ambiguous id across data sources: {args.id}")
            emit(bounded_record(matches[0]), args.json)
        else:
            if not 1 <= args.limit <= 20:
                raise ValueError("--limit must be between 1 and 20")
            if not args.query.strip() or len(args.query) > 500:
                raise ValueError("Query must contain 1–500 characters")
            ranked = [(rank(record, args.query), record) for record in records]
            ranked = sorted((item for item in ranked if item[0] > 0),
                            key=lambda item: (-item[0], item[1]["provenance"], item[1]["id"]))
            emit({"query": args.query, "match_count": len(ranked),
                  "matches": [summary(record, args.query, score) for score, record in ranked[:args.limit]]}, args.json)
        return 0
    except (OSError, ValueError, TypeError, KeyError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())
