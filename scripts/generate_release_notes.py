#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from pathlib import Path


def extract_section(changelog: Path, version: str) -> list[str]:
    lines = changelog.read_text(encoding="utf-8").splitlines()
    sections: dict[str, tuple[int, int | None]] = {}
    order: list[str] = []

    current_key: str | None = None
    current_start: int | None = None

    for idx, line in enumerate(lines):
        if line.startswith("## ["):
            # Finish previous
            if current_key is not None and current_start is not None:
                start, _ = sections[current_key]
                sections[current_key] = (start, idx)
            # New section key
            try:
                key = line.split("[", 1)[1].split("]", 1)[0].strip()
            except Exception:
                continue
            current_key = key
            current_start = idx + 1
            sections[current_key] = (current_start, None)
            order.append(current_key)

    # Close last
    if current_key is not None and current_start is not None:
        start, _ = sections[current_key]
        sections[current_key] = (start, len(lines))

    if version not in sections:
        raise SystemExit(f"Version '{version}' not found in {changelog}")

    start, end = sections[version]
    body = lines[start:end]

    # Trim leading/trailing blank lines
    while body and not body[0].strip():
        body.pop(0)
    while body and not body[-1].strip():
        body.pop()
    return body


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Generate release notes from CHANGELOG.md")
    p.add_argument("--version", help="Version without 'v' prefix (e.g., 0.2.0)")
    p.add_argument("--changelog", default="docs/CHANGELOG.md", help="Path to changelog file")
    p.add_argument("--out", help="Output file to write. Prints to stdout if omitted")
    args = p.parse_args(argv)

    version = args.version or os.getenv("GITHUB_REF_NAME", "").lstrip("v")
    if not version:
        raise SystemExit("No version provided and GITHUB_REF_NAME not set")

    body = extract_section(Path(args.changelog), version)
    output = "\n".join(body).rstrip() + "\n"

    if args.out:
        Path(args.out).write_text(output, encoding="utf-8")
    else:
        print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
