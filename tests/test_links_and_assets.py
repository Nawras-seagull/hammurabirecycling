#!/usr/bin/env python3
"""
test_links_and_assets.py — finds broken internal links and missing
referenced assets (images, video, CSS, JS) across every HTML page.

Standalone: stdlib only, no dependency on any other test file.

For a static site, this is the single most common launch-blocker: an
image renamed on disk but not in the HTML, a link to a page that was
never built, a typo in a path. This script does not check external
(http/https) links — that would require network access and is a
separate, slower kind of check; run a link-checker service for that
if you want it.

Usage:
    python3 test_links_and_assets.py [--root .]
Exit code is non-zero if any internal link or asset reference is broken.
"""
import argparse
import os
import re
import sys


ATTR_PATTERN = re.compile(r'\b(?:href|src)\s*=\s*"([^"]+)"', re.IGNORECASE)
SRCSET_PATTERN = re.compile(r'\bsrcset\s*=\s*"([^"]+)"', re.IGNORECASE)

SKIP_PREFIXES = ("http://", "https://", "mailto:", "tel:", "javascript:", "data:", "#", "//")


def find_html_files(root):
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        if "node_modules" in dirpath or "/.git" in dirpath:
            continue
        for name in filenames:
            if name.endswith(".html"):
                out.append(os.path.join(dirpath, name))
    return sorted(out)


def resolve_internal_path(root, ref):
    """Resolve a root-relative path like /about-us/ or /assets/x.jpg
    against the site root on disk. Returns the resolved filesystem path
    or None if it's not an internal, resolvable reference."""
    ref = ref.split("#")[0].split("?")[0]
    if not ref.startswith("/"):
        return None  # only checking root-relative internal links here
    rel = ref.lstrip("/")
    if rel == "":
        rel = "index.html"
    candidate = os.path.join(root, rel)
    if os.path.isdir(candidate):
        candidate = os.path.join(candidate, "index.html")
    return candidate


def extract_references(html):
    refs = set()
    for m in ATTR_PATTERN.finditer(html):
        refs.add(m.group(1).strip())
    for m in SRCSET_PATTERN.finditer(html):
        # srcset can contain multiple "url descriptor, url descriptor"
        parts = m.group(1).split(",")
        for part in parts:
            url = part.strip().split(" ")[0]
            if url:
                refs.add(url)
    return refs


def main():
    parser = argparse.ArgumentParser(description="Check for broken internal links and missing assets.")
    parser.add_argument("--root", default=".", help="Path to the site root (default: current directory)")
    args = parser.parse_args()
    root = args.root

    files = find_html_files(root)
    if not files:
        print(f"No .html files found under {root}")
        sys.exit(1)

    total_broken = 0
    for path in files:
        with open(path, "r", encoding="utf-8") as f:
            html = f.read()

        broken_here = []
        for ref in sorted(extract_references(html)):
            if ref.startswith(SKIP_PREFIXES):
                continue
            resolved = resolve_internal_path(root, ref)
            if resolved is None:
                continue
            if not os.path.isfile(resolved):
                broken_here.append((ref, resolved))

        if broken_here:
            total_broken += len(broken_here)
            print(f"\nFAIL {path}")
            for ref, resolved in broken_here:
                print(f"   - \"{ref}\" does not resolve to a file (looked for {resolved})")
        else:
            print(f"OK   {path}")

    print(f"\nChecked {len(files)} file(s), {total_broken} broken reference(s) found.")
    sys.exit(1 if total_broken else 0)


if __name__ == "__main__":
    main()