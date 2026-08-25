#!/usr/bin/env python3
"""
test_json_ld.py — validates every JSON-LD block on every page.

Standalone: stdlib only, no dependency on any other test file.

A JSON-LD block with a syntax error doesn't break page rendering (browsers
just silently ignore it), which is exactly why it needs its own check —
nothing else will catch a broken <script type="application/ld+json">
until Google Search Console flags it days later.

Checks:
  - every application/ld+json block is parseable JSON
  - it has @context and @type
  - if @type is LocalBusiness, the fields a search result actually
    uses are present: name, telephone, address

Usage:
    python3 test_json_ld.py [--root .]
Exit code is non-zero if any check fails.
"""
import argparse
import json
import os
import re
import sys


def find_html_files(root):
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        if "node_modules" in dirpath or "/.git" in dirpath:
            continue
        for name in filenames:
            if name.endswith(".html"):
                out.append(os.path.join(dirpath, name))
    return sorted(out)


BLOCK_PATTERN = re.compile(
    r'<script\s+type="application/ld\+json">(.*?)</script>', re.IGNORECASE | re.DOTALL
)


def check_file(path):
    problems = []
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    blocks = BLOCK_PATTERN.findall(content)
    if not blocks:
        return [f"no JSON-LD found on this page (expected at least one)"]

    for i, raw in enumerate(blocks, start=1):
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            problems.append(f"block {i}: invalid JSON — {e}")
            continue

        if "@context" not in data:
            problems.append(f"block {i}: missing @context")
        if "@type" not in data:
            problems.append(f"block {i}: missing @type")

        if data.get("@type") == "LocalBusiness":
            for field in ["name", "telephone", "address"]:
                if not data.get(field):
                    problems.append(f"block {i} (LocalBusiness): missing or empty \"{field}\"")

        if data.get("@type") == "BreadcrumbList":
            items = data.get("itemListElement", [])
            if not items:
                problems.append(f"block {i} (BreadcrumbList): itemListElement is empty")
            else:
                positions = [it.get("position") for it in items]
                if positions != sorted(positions):
                    problems.append(f"block {i} (BreadcrumbList): positions are not in order: {positions}")

    return problems


def main():
    parser = argparse.ArgumentParser(description="Validate JSON-LD structured data.")
    parser.add_argument("--root", default=".", help="Path to the site root (default: current directory)")
    args = parser.parse_args()

    files = find_html_files(args.root)
    if not files:
        print(f"No .html files found under {args.root}")
        sys.exit(1)

    total = 0
    for path in files:
        problems = check_file(path)
        if problems:
            total += len(problems)
            print(f"\nFAIL {path}")
            for p in problems:
                print(f"   - {p}")
        else:
            print(f"OK   {path}")

    print(f"\nChecked {len(files)} file(s), {total} problem(s) found.")
    sys.exit(1 if total else 0)


if __name__ == "__main__":
    main()