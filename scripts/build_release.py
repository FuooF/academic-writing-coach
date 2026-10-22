#!/usr/bin/env python3
"""Build reproducible, allowlisted source/runtime archives without bundling private corpora."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
KNOWN_FILES = {
    "SKILL.md", "README.md", "README.zh-CN.md", "LICENSE", "THIRD_PARTY_NOTICES.md", "SOURCES.md",
    "VERSION", ".gitignore", ".github/workflows/ci.yml", ".github/workflows/release.yml",
    "agents/openai.yaml", "references/moves.json", "references/revision-rubric.md",
    "examples/walkthrough.md", "evals/cases.json", "docs/PUBLISHING.md", "release-manifest.json",
    "scripts/lookup.py", "scripts/import_local.py", "scripts/install.py", "scripts/build_release.py",
    "tests/test_tooling.py",
}


def checked_file(relative: str) -> Path:
    if not isinstance(relative, str):
        raise ValueError("Manifest paths must be strings")
    parts = PurePosixPath(relative)
    if parts.is_absolute() or ".." in parts.parts or "\\" in relative or ":" in relative:
        raise ValueError(f"Unsafe manifest path: {relative}")
    if relative not in KNOWN_FILES:
        raise ValueError(f"Unknown release entry (review the explicit allowlist): {relative}")
    if "private" in parts.name.casefold() or parts.name == ".local-data-config.json":
        raise ValueError(f"Private data cannot be released: {relative}")
    path = ROOT / relative
    cursor = path
    while cursor != ROOT:
        if cursor.is_symlink() or getattr(cursor, "is_junction", lambda: False)():
            raise ValueError(f"Symlinks cannot be released: {relative}")
        cursor = cursor.parent
    if not path.is_file():
        raise ValueError(f"Missing release entry: {relative}")
    if not path.resolve().is_relative_to(ROOT):
        raise ValueError(f"Release entry resolves outside the repository: {relative}")
    return path


def load_manifest() -> dict:
    with (ROOT / "release-manifest.json").open(encoding="utf-8-sig") as stream:
        manifest = json.load(stream)
    if not isinstance(manifest, dict) or set(manifest) != {"schema_version", "package_name", "files", "runtime_files"}:
        raise ValueError("Manifest must contain exactly schema_version, package_name, files, runtime_files")
    if manifest["schema_version"] != 1 or manifest["package_name"] != "academic-writing-coach":
        raise ValueError("Unsupported manifest schema or package name")
    for key in ("files", "runtime_files"):
        values = manifest[key]
        if not isinstance(values, list) or not values or not all(isinstance(item, str) for item in values):
            raise ValueError(f"Manifest {key} must be a nonempty array of paths")
        if len(set(values)) != len(values):
            raise ValueError(f"Duplicate paths in manifest {key}")
        for relative in values:
            checked_file(relative)
    if set(manifest["files"]) != KNOWN_FILES:
        raise ValueError("Source manifest must match the reviewed release allowlist exactly")
    if not set(manifest["runtime_files"]).issubset(manifest["files"]):
        raise ValueError("Runtime files must also appear in the source archive")
    if "SKILL.md" not in manifest["runtime_files"]:
        raise ValueError("Runtime archive needs SKILL.md")
    return manifest


def write_archive(destination: Path, members: list[str], name: str) -> None:
    with zipfile.ZipFile(destination, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for relative in sorted(members):
            content = checked_file(relative).read_bytes()
            info = zipfile.ZipInfo(f"{name}/{relative}", date_time=(2026, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, content, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="Archive destination outside the repository")
    args = parser.parse_args(argv)
    try:
        output = args.output.expanduser().resolve()
        if output == ROOT or ROOT in output.parents:
            raise ValueError("--output must be outside the source repository")
        manifest = load_manifest()
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        if not re.fullmatch(r"\d+\.\d+\.\d+(?:-[a-zA-Z0-9.-]+)?", version):
            raise ValueError("VERSION must contain a semantic version such as 0.1.0")
        base = f"{manifest['package_name']}-{version}"
        paths = [output / f"{base}-source.zip", output / f"{base}.skill", output / f"{base}-SHA256SUMS.txt"]
        if any(path.exists() or path.is_symlink() for path in paths):
            raise ValueError("Release output already exists; choose a new output directory")
        output.mkdir(parents=True, exist_ok=True)
        write_archive(paths[0], manifest["files"], manifest["package_name"])
        write_archive(paths[1], manifest["runtime_files"], manifest["package_name"])
        checksums = [f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}" for path in paths[:2]]
        with paths[2].open("x", encoding="ascii", newline="\n") as stream:
            stream.write("\n".join(checksums) + "\n")
        print(json.dumps({"version": version, "source_files": len(manifest["files"]),
                          "runtime_files": len(manifest["runtime_files"]),
                          "artifacts": [str(path) for path in paths]}, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, TypeError, KeyError, zipfile.BadZipFile) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())
