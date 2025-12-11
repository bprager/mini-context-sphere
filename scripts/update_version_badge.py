#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
from pathlib import Path


def infer_color(version: str, override: str | None = None) -> str:
    """Infer right-hand badge color from version string.

    Mapping (case-insensitive):
    - alpha / PEP440 "aN" suffix -> red (#e05d44)
    - beta / PEP440 "bN" suffix -> orange (#fe7d37)
    - rc / release candidate / pre -> yellow (#dfb317)
    - dev / nightly / snapshot -> blue (#007ec6)
    - otherwise (stable) -> green (#2ea44f)

    If override is provided, it may be a named color (green, orange, yellow, red, blue)
    or a hex like "#33aa44".
    """
    if override:
        named = {
            "green": "#2ea44f",
            "orange": "#fe7d37",
            "yellow": "#dfb317",
            "red": "#e05d44",
            "blue": "#007ec6",
        }
        return named.get(override.lower(), override)

    v = version.lower()
    # PEP440 pre-release suffixes and common markers
    if "alpha" in v or re.search(r"a\d*$", v):
        return "#e05d44"  # red
    if "beta" in v or re.search(r"b\d*$", v):
        return "#fe7d37"  # orange
    if "rc" in v or "candidate" in v or "pre" in v or re.search(r"rc\d*$", v):
        return "#dfb317"  # yellow
    if any(x in v for x in ("dev", "nightly", "snapshot")):
        return "#007ec6"  # blue
    return "#2ea44f"  # green


def render_svg(version: str, color: str) -> str:
    # Very simple flat-style badge. Fixed widths sufficient for typical vX.Y.Z.
    label = "version"
    left_width = 62  # approx for "version"
    # Allow a bit more room for suffixes like -beta.1
    right_width = max(64, 8 * len(version))
    total = left_width + right_width
    svg = f"""
<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"{total}\" height=\"20\" role=\"img\"
  aria-label=\"{label}: {version}\">
  <title>{label}: {version}</title>
  <linearGradient id=\"s\" x2=\"0\" y2=\"100%\">
    <stop offset=\"0\" stop-color=\"#bbb\" stop-opacity=\".1\"/>
    <stop offset=\"1\" stop-opacity=\".1\"/>
  </linearGradient>
  <mask id=\"m\"><rect width=\"{total}\" height=\"20\" rx=\"3\" fill=\"#fff\"/></mask>
  <g mask=\"url(#m)\">
    <rect width=\"{left_width}\" height=\"20\" fill=\"#555\"/>
    <rect x=\"{left_width}\" width=\"{right_width}\" height=\"20\" fill=\"{color}\"/>
    <rect width=\"{total}\" height=\"20\" fill=\"url(#s)\"/>
  </g>
  <g fill=\"#fff\" text-anchor=\"middle\"
     font-family=\"Verdana,Geneva,DejaVu Sans,sans-serif\" font-size=\"11\">
    <text x=\"{left_width / 2:.1f}\" y=\"14\">{label}</text>
    <text x=\"{left_width + right_width / 2:.1f}\" y=\"14\">{version}</text>
  </g>
  <svg xmlns=\"http://www.w3.org/2000/svg\"/>
</svg>
""".strip()
    return svg


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Update static version badge SVG")
    p.add_argument("--version", help="Version string (e.g., 1.0.0 or v1.0.0)")
    p.add_argument("--out", default="docs/badges/version.svg", help="Output SVG path")
    p.add_argument("--color", help="Override badge color (name or hex)")
    args = p.parse_args(argv)

    ver = args.version or os.getenv("GITHUB_REF_NAME", "").lstrip("v")
    if not ver:
        raise SystemExit("No version provided and GITHUB_REF_NAME not set")
    ver_out = f"v{ver}" if not ver.startswith("v") else ver

    color = infer_color(ver_out, args.color)
    svg = render_svg(ver_out, color)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    current = out_path.read_text(encoding="utf-8") if out_path.exists() else ""
    if current.strip() != svg.strip():
        out_path.write_text(svg, encoding="utf-8")
        print(f"Updated {out_path} to {ver_out}")
    else:
        print(f"No change for {out_path} ({ver_out})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
