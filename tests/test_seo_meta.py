#!/usr/bin/env python3
"""
test_seo_meta.py — checks the meta tags that actually matter for a
brochure site going live: title, description, canonical, Open Graph,
hreflang, plus sitemap.xml/robots.txt consistency with what's on disk.

Standalone: stdlib only, no dependency on any other test file.

Usage:
    python3 test_seo_meta.py [--root .]
Exit code is non-zero if any check fails.
"""
import argparse
import os
import re
import sys
import xml.etree.ElementTree as ET


def find_html_files(root):
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        if "node_modules" in dirpath or "/.git" in dirpath:
            continue
        for name in filenames:
            if name.endswith(".html"):
                out.append(os.path.join(dirpath, name))
    return sorted(out)


def check_page_meta(path):
    problems = []
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    title_m = re.search(r"<title>(.*?)</title>", content, re.IGNORECASE | re.DOTALL)
    if not title_m or not title_m.group(1).strip():
        problems.append("missing <title>")
    elif len(title_m.group(1).strip()) > 65:
        problems.append(f"<title> is {len(title_m.group(1).strip())} chars — search engines usually truncate past ~60-65")

    desc_m = re.search(r'<meta\s+name="description"\s+content="([^"]*)"', content, re.IGNORECASE)
    if not desc_m or not desc_m.group(1).strip():
        problems.append("missing meta description")

    canon_m = re.search(r'<link\s+rel="canonical"\s+href="([^"]+)"', content, re.IGNORECASE)
    if not canon_m:
        problems.append("missing <link rel=\"canonical\">")
    elif not canon_m.group(1).startswith("https://"):
        problems.append(f"canonical URL is not absolute https://: {canon_m.group(1)}")

    for og_prop in ["og:title", "og:description", "og:image", "og:url", "og:type"]:
        pattern = rf'<meta\s+property="{re.escape(og_prop)}"\s+content="([^"]*)"'
        m = re.search(pattern, content, re.IGNORECASE)
        if not m or not m.group(1).strip():
            problems.append(f"missing or empty {og_prop}")

    if not re.search(r'<meta\s+name="viewport"', content, re.IGNORECASE):
        problems.append("missing <meta name=\"viewport\"> — page won't be mobile-responsive")

    # hreflang: if this page declares any, it should declare a full set
    hreflangs = re.findall(r'hreflang="([^"]+)"', content, re.IGNORECASE)
    if hreflangs:
        if "x-default" not in hreflangs:
            problems.append(f"has hreflang alternates {hreflangs} but no \"x-default\" entry")

    return problems


def check_sitemap(root):
    problems = []
    sitemap_path = os.path.join(root, "sitemap.xml")
    if not os.path.isfile(sitemap_path):
        problems.append((sitemap_path, "sitemap.xml not found"))
        return problems

    try:
        tree = ET.parse(sitemap_path)
    except ET.ParseError as e:
        problems.append((sitemap_path, f"sitemap.xml is not valid XML: {e}"))
        return problems

    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    locs = [el.text.strip() for el in tree.getroot().findall("sm:url/sm:loc", ns) if el.text]

    if not locs:
        problems.append((sitemap_path, "no <url><loc> entries found"))

    for loc in locs:
        # turn an absolute URL into a local path check
        m = re.match(r"https?://[^/]+(/.*)", loc)
        if not m:
            problems.append((sitemap_path, f"non-absolute or malformed URL: {loc}"))
            continue
        rel = m.group(1).lstrip("/")
        if rel == "":
            rel = "index.html"
        elif rel.endswith("/"):
            rel = rel + "index.html"
        local_path = os.path.join(root, rel)
        if not os.path.isfile(local_path):
            problems.append((sitemap_path, f"sitemap lists {loc} but {local_path} does not exist on disk"))

    return problems


def check_robots(root):
    problems = []
    robots_path = os.path.join(root, "robots.txt")
    if not os.path.isfile(robots_path):
        problems.append((robots_path, "robots.txt not found"))
        return problems
    with open(robots_path, "r", encoding="utf-8") as f:
        content = f.read()
    if "sitemap:" not in content.lower():
        problems.append((robots_path, "robots.txt does not reference the sitemap"))
    if re.search(r"disallow:\s*/\s*$", content, re.IGNORECASE | re.MULTILINE):
        problems.append((robots_path, "robots.txt has \"Disallow: /\" — this would block the entire site from search engines"))
    return problems


def main():
    parser = argparse.ArgumentParser(description="SEO meta tag and sitemap/robots checks.")
    parser.add_argument("--root", default=".", help="Path to the site root (default: current directory)")
    args = parser.parse_args()
    root = args.root

    files = find_html_files(root)
    if not files:
        print(f"No .html files found under {root}")
        sys.exit(1)

    total = 0
    for path in files:
        problems = check_page_meta(path)
        if problems:
            total += len(problems)
            print(f"\nFAIL {path}")
            for p in problems:
                print(f"   - {p}")
        else:
            print(f"OK   {path}")

    for label, checker in [("sitemap.xml", check_sitemap), ("robots.txt", check_robots)]:
        problems = checker(root)
        if problems:
            total += len(problems)
            print(f"\nFAIL — {label}")
            for path, msg in problems:
                print(f"   - {path}: {msg}")
        else:
            print(f"OK   — {label}")

    print(f"\nChecked {len(files)} page(s), {total} problem(s) found.")
    sys.exit(1 if total else 0)


if __name__ == "__main__":
    main()