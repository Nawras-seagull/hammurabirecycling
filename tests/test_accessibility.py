#!/usr/bin/env python3
"""
test_accessibility.py — the accessibility checks that can be verified
from the HTML alone, without a browser or screen reader.

Standalone: stdlib only, no dependency on any other test file.

Checks per page:
  - <html> has a lang attribute
  - every <img> has an alt attribute (present, even if empty for
    purely decorative images — an image with no alt at all is the bug)
  - every text/email/tel/password/textarea/select input with an id has
    a matching <label for="..."> OR an aria-label/aria-labelledby
  - every icon-only <button> (no visible text between the tags) has
    an aria-label
  - a "skip to content" link exists
  - heading levels don't jump (e.g. an <h3> appearing before any <h2>)

This is NOT a substitute for testing with an actual screen reader or
running axe-core/Lighthouse in a browser — it catches the structural
mistakes that are easy to make by hand and easy to check without one.

Usage:
    python3 test_accessibility.py [--root .]
Exit code is non-zero if any check fails.
"""
import argparse
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


def check_file(path):
    problems = []
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    if not re.search(r'<html\b[^>]*\blang\s*=\s*"[^"]+"', content, re.IGNORECASE):
        problems.append("<html> is missing a lang attribute")

    for m in re.finditer(r"<img\b([^>]*)>", content, re.IGNORECASE):
        attrs = m.group(1)
        if not re.search(r'\balt\s*=\s*"', attrs):
            snippet = m.group(0)[:100]
            problems.append(f"<img> with no alt attribute at all: {snippet}")

    # collect id -> associated label check
    labelled_ids = set(re.findall(r'<label\b[^>]*\bfor\s*=\s*"([^"]+)"', content, re.IGNORECASE))
    for m in re.finditer(r"<(input|textarea|select)\b([^>]*)>", content, re.IGNORECASE):
        tag, attrs = m.group(1), m.group(2)
        type_m = re.search(r'type\s*=\s*"([^"]+)"', attrs, re.IGNORECASE)
        input_type = type_m.group(1).lower() if type_m else "text"
        if input_type in ("hidden", "submit", "button"):
            continue
        id_m = re.search(r'\bid\s*=\s*"([^"]+)"', attrs)
        has_aria = re.search(r'\baria-label(ledby)?\s*=\s*"', attrs)
        if not has_aria:
            if not id_m:
                problems.append(f"<{tag}> has no id and no aria-label — a <label> can't be associated with it: {m.group(0)[:100]}")
            elif id_m.group(1) not in labelled_ids:
                problems.append(f"<{tag} id=\"{id_m.group(1)}\"> has no matching <label for=\"{id_m.group(1)}\"> and no aria-label")

    for m in re.finditer(r"<button\b([^>]*)>(.*?)</button>", content, re.IGNORECASE | re.DOTALL):
        attrs, inner = m.group(1), m.group(2)
        visible_text = re.sub(r"<[^>]+>", "", inner).strip()
        has_aria_label = re.search(r'\baria-label\s*=\s*"[^"]+"', attrs)
        if not visible_text and not has_aria_label:
            problems.append(f"icon-only <button> with no aria-label: {m.group(0)[:100]}")

    if not re.search(r'class="skip-link"', content) and not re.search(r'href="#main"', content):
        problems.append("no \"skip to content\" link found")

    headings = re.findall(r"<h([1-6])\b", content, re.IGNORECASE)
    levels = [int(h) for h in headings]
    seen_max = 0
    for lvl in levels:
        if lvl > seen_max + 1 and seen_max != 0:
            problems.append(f"heading level jumps from h{seen_max} to h{lvl} without an h{seen_max+1} in between")
        seen_max = max(seen_max, lvl)

    return problems


def main():
    parser = argparse.ArgumentParser(description="Basic static accessibility checks.")
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
    print("Note: this script cannot check color contrast or screen-reader")
    print("behavior — run a browser tool (e.g. axe DevTools, Lighthouse) for those.")
    sys.exit(1 if total else 0)


if __name__ == "__main__":
    main()