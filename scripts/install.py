#!/usr/bin/env python3
"""Install the runtime skill without downloading dependencies or replacing an existing skill."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
NAME = "academic-writing-coach"
RUNTIME_FILES = (
    "SKILL.md", "agents/openai.yaml", "references/moves.json", "references/revision-rubric.md",
    "scripts/lookup.py", "scripts/import_local.py", "LICENSE", "THIRD_PARTY_NOTICES.md",
    "SOURCES.md", "README.md", "README.zh-CN.md", "VERSION",
    "scripts/install.py", "docs/PUBLISHING.md", "examples/walkthrough.md", "evals/cases.json",
)


def checked_source(relative: str) -> Path:
    source = ROOT / relative
    cursor = source
    while cursor != ROOT:
        if cursor.is_symlink() or getattr(cursor, "is_junction", lambda: False)():
            raise ValueError(f"Refusing symlink in runtime: {relative}")
        cursor = cursor.parent
    if not source.is_file():
        raise ValueError(f"Required runtime file is missing: {relative}")
    if not source.resolve().is_relative_to(ROOT):
        raise ValueError(f"Runtime file resolves outside the repository: {relative}")
    return source


def default_destination(target: str) -> Path:
    if target == "codex":
        codex_home = os.environ.get("CODEX_HOME")
        return (Path(codex_home).expanduser() if codex_home else Path.home() / ".codex") / "skills"
    return Path.home() / ".claude" / "skills"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", choices=("codex", "claude"), required=True)
    parser.add_argument("--destination", type=Path, help="Custom skills root; the skill gets its own subdirectory")
    parser.add_argument("--data-dir", type=Path, help="Existing private-data directory to associate with this installation")
    args = parser.parse_args(argv)
    try:
        sources = [(name, checked_source(name)) for name in RUNTIME_FILES]
        destination_root = (args.destination or default_destination(args.target)).expanduser().resolve()
        destination = destination_root / NAME
        if destination.exists() or destination.is_symlink():
            raise ValueError(f"Destination already exists; no files were replaced: {destination}")
        data_directory = None
        if args.data_dir:
            data_directory = args.data_dir.expanduser().resolve()
            if not data_directory.is_dir():
                raise ValueError("--data-dir must name an existing directory")
            if data_directory == destination or destination in data_directory.parents:
                raise ValueError("Private data must stay outside the installed skill directory")
        if destination == ROOT or ROOT in destination.parents:
            raise ValueError("Install destination must be outside the source repository")
        destination_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=".academic-writing-coach-", dir=destination_root) as staging:
            staged_skill = Path(staging) / NAME
            staged_skill.mkdir()
            for relative, source in sources:
                output = staged_skill / relative
                output.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, output)
            if data_directory:
                (staged_skill / ".local-data-config.json").write_text(
                    json.dumps({"data_dir": str(data_directory)}, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")
            # A nonempty destination directory is never replaced by this rename.
            # Recheck to cover another process installing during the staging copy.
            if destination.exists() or destination.is_symlink():
                raise ValueError(f"Destination appeared during installation; refusing to replace it: {destination}")
            staged_skill.rename(destination)
        print(json.dumps({"installed": str(destination), "target": args.target,
                          "runtime_files": len(sources), "local_data_configured": data_directory is not None},
                         ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())
