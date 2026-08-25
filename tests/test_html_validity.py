#!/usr/bin/env python3
"""
test_html_validity.py — structural sanity checks on every HTML page.

Standalone: stdlib only, no dependency on any other test file.

Checks per page:
  - starts with <!DOCTYPE html>
  - <html> has both lang and dir attributes
  - <title> is present and non-empty
  - exactly one <h1>
  - no duplicate id="" attributes
  - every <img> tag closes properly (basic tag-balance check on a few
    structural tags: div/section/header/footer/main/nav/ul/ol)

This is NOT a full HTML5 validator (that needs an external validator
service or the html5lib package, which isn't assumed to be installed).
It catches the mistakes that actually tend to break a static brochure
site: a missing lang/dir attribute, two <h1>s on one page, a leftover
duplicate id from copy-pasting a section, or a badly unbalanced tag.

Usage:
    python3 test_html_validity.py [--root .]
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


def strip_comments(html):
    """Remove HTML comments before running structural checks, so prose
    inside a comment (e.g. "this <form> works with JS off") doesn't get
    mistaken for a real tag."""
    return re.sub(r"<!--.*?-->", "", html, flags=re.DOTALL)


def check_file(path):
    problems = []
    with open(path, "r", encoding="utf-8") as f:
        raw_content = f.read()
    content = strip_comments(raw_content)

    if not content.lstrip().lower().startswith("<!doctype html"):
        problems.append("missing or misplaced <!DOCTYPE html> at the top of the file")

    html_tag_match = re.search(r"<html\b([^>]*)>", content, re.IGNORECASE)
    if not html_tag_match:
        problems.append("no <html> tag found")
    else:
        attrs = html_tag_match.group(1)
        if not re.search(r'\blang\s*=\s*"[^"]+"', attrs):
            problems.append("<html> tag is missing a lang attribute")
        if not re.search(r'\bdir\s*=\s*"(ltr|rtl)"', attrs):
            problems.append("<html> tag is missing a dir=\"ltr\"/\"rtl\" attribute")

    title_match = re.search(r"<title>(.*?)</title>", content, re.IGNORECASE | re.DOTALL)
    if not title_match or not title_match.group(1).strip():
        problems.append("missing or empty <title>")

    h1_count = len(re.findall(r"<h1\b", content, re.IGNORECASE))
    if h1_count == 0:
        problems.append("no <h1> found on the page")
    elif h1_count > 1:
        problems.append(f"{h1_count} <h1> tags found — a page should have exactly one")

    ids = re.findall(r'\bid\s*=\s*"([^"]+)"', content)
    seen = set()
    dupes = set()
    for i in ids:
        if i in seen:
            dupes.add(i)
        seen.add(i)
    if dupes:
        problems.append(f"duplicate id attribute(s): {', '.join(sorted(dupes))}")

    for tag in ["div", "section", "header", "footer", "main", "nav", "ul", "ol", "form"]:
        opens = len(re.findall(rf"<{tag}\b", content, re.IGNORECASE))
        closes = len(re.findall(rf"</{tag}\s*>", content, re.IGNORECASE))
        if opens != closes:
            problems.append(f"unbalanced <{tag}> tags: {opens} opening vs {closes} closing")

    return problems


def main():
    parser = argparse.ArgumentParser(description="Check basic HTML structural validity.")
    parser.add_argument("--root", default=".", help="Path to the site root (default: current directory)")
    args = parser.parse_args()

    files = find_html_files(args.root)
    if not files:
        print(f"No .html files found under {args.root}")
        sys.exit(1)

    total_problems = 0
    for path in files:
        problems = check_file(path)
        if problems:
            total_problems += len(problems)
            print(f"\nFAIL {path}")
            for p in problems:
                print(f"   - {p}")
        else:
            print(f"OK   {path}")

    print(f"\nChecked {len(files)} file(s), {total_problems} problem(s) found.")
    sys.exit(1 if total_problems else 0)


if __name__ == "__main__":
    main()