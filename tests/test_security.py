#!/usr/bin/env python3
"""
test_security.py — the security checks that actually apply to a static
HTML/CSS/JS site with a third-party form (Formspree) and no backend.

Standalone: stdlib only, no dependency on any other test file.

What this checks:
  1. No mixed content — every asset/link reference is https:// or
     root-relative, never a bare http:// URL.
  2. Every target="_blank" link includes rel="noopener" (prevents the
     opened page from getting a handle back to window.opener).
  3. main.js (and any other JS file) doesn't use dangerous sinks:
     innerHTML assignment, document.write, eval, new Function.
  4. No obvious hardcoded secrets/API keys committed anywhere in the
     project (common key-shaped patterns).
  5. netlify.toml declares the baseline security headers.
  6. Every <form> uses method="POST" and has a honeypot field.
  7. No form action is left pointing at plain http:// (must be https).

What this deliberately does NOT do: this is not a penetration test,
a dependency vulnerability scan, or a TLS/cipher check — none of those
apply to a static site with no server-side code and no dependencies.
For a post-deploy check of the actual HTTP response headers Netlify is
sending, see test_headers_live.py.

Usage:
    python3 test_security.py [--root .]
Exit code is non-zero if any check fails.
"""
import argparse
import os
import re
import sys


def find_files(root, extensions):
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        if "node_modules" in dirpath or "/.git" in dirpath:
            continue
        for name in filenames:
            if name.endswith(extensions):
                out.append(os.path.join(dirpath, name))
    return sorted(out)


SECRET_PATTERNS = [
    (re.compile(r"AKIA[0-9A-Z]{16}"), "AWS access key"),
    (re.compile(r"sk_live_[0-9a-zA-Z]{16,}"), "Stripe live secret key"),
    (re.compile(r"AIza[0-9A-Za-z\-_]{35}"), "Google API key"),
    (re.compile(r"ghp_[0-9A-Za-z]{36}"), "GitHub personal access token"),
    (re.compile(r"xox[baprs]-[0-9A-Za-z-]{10,}"), "Slack token"),
    (re.compile(r"-----BEGIN (RSA|EC|OPENSSH|PRIVATE) KEY-----"), "private key material"),
]

DANGEROUS_JS_SINKS = [
    (re.compile(r"\.innerHTML\s*="), ".innerHTML assignment (XSS risk if it ever includes user input)"),
    (re.compile(r"\bdocument\.write\s*\("), "document.write("),
    (re.compile(r"(?<![\w.])eval\s*\("), "eval("),
    (re.compile(r"new\s+Function\s*\("), "new Function("),
]


def check_mixed_content(html_files):
    problems = []
    for path in html_files:
        with open(path, "r", encoding="utf-8") as f:
            content = strip_comments(f.read())
        for m in re.finditer(r'(?:href|src)\s*=\s*"(http://[^"]+)"', content, re.IGNORECASE):
            problems.append((path, f'insecure http:// resource: "{m.group(1)}"'))
    return problems


def check_target_blank_noopener(html_files):
    problems = []
    for path in html_files:
        with open(path, "r", encoding="utf-8") as f:
            content = strip_comments(f.read())
        for m in re.finditer(r"<a\b[^>]*\btarget\s*=\s*\"_blank\"[^>]*>", content, re.IGNORECASE):
            tag = m.group(0)
            if "noopener" not in tag.lower():
                snippet = tag[:80] + ("…" if len(tag) > 80 else "")
                problems.append((path, f"target=\"_blank\" link missing rel=\"noopener\": {snippet}"))
    return problems


def check_js_sinks(js_files):
    problems = []
    for path in js_files:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        for pattern, label in DANGEROUS_JS_SINKS:
            for m in pattern.finditer(content):
                line_no = content[:m.start()].count("\n") + 1
                problems.append((path, f"line {line_no}: uses {label}"))
    return problems


def check_secrets(all_files):
    problems = []
    for path in all_files:
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except (UnicodeDecodeError, IsADirectoryError):
            continue
        for pattern, label in SECRET_PATTERNS:
            if pattern.search(content):
                problems.append((path, f"looks like a hardcoded {label} — remove and rotate it"))
    return problems


def check_netlify_headers(root):
    problems = []
    toml_path = os.path.join(root, "netlify.toml")
    required = ["X-Frame-Options", "X-Content-Type-Options", "Referrer-Policy"]
    if not os.path.isfile(toml_path):
        problems.append((toml_path, "netlify.toml not found — baseline security headers won't be set"))
        return problems
    with open(toml_path, "r", encoding="utf-8") as f:
        content = f.read()
    for header in required:
        if header not in content:
            problems.append((toml_path, f"missing recommended header: {header}"))
    return problems


def strip_comments(html):
    """Remove HTML comments so prose inside a comment (e.g. mentioning
    "<form>" in an explanation) isn't mistaken for a real tag."""
    return re.sub(r"<!--.*?-->", "", html, flags=re.DOTALL)


def check_forms(html_files):
    problems = []
    for path in html_files:
        with open(path, "r", encoding="utf-8") as f:
            content = strip_comments(f.read())
        for m in re.finditer(r"<form\b[^>]*>", content, re.IGNORECASE):
            tag = m.group(0)
            if not re.search(r'method\s*=\s*"post"', tag, re.IGNORECASE):
                problems.append((path, f"<form> is missing method=\"POST\": {tag[:80]}"))
            action_m = re.search(r'action\s*=\s*"(http://[^"]+)"', tag, re.IGNORECASE)
            if action_m:
                problems.append((path, f"<form action> uses insecure http://: {action_m.group(1)}"))
        # honeypot field — look for the hidden trap input anywhere in the file
        if "<form" in content.lower() and "_gotcha" not in content:
            problems.append((path, "page has a <form> but no honeypot (_gotcha) field found"))
    return problems


def main():
    parser = argparse.ArgumentParser(description="Security checks appropriate for a static site.")
    parser.add_argument("--root", default=".", help="Path to the site root (default: current directory)")
    args = parser.parse_args()
    root = args.root

    html_files = find_files(root, (".html",))
    js_files = find_files(root, (".js",))
    all_files = find_files(root, (".html", ".js", ".json", ".toml", ".txt", ".xml", ".webmanifest"))

    if not html_files:
        print(f"No .html files found under {root}")
        sys.exit(1)

    checks = [
        ("Mixed content (http:// resources)", check_mixed_content(html_files)),
        ("target=\"_blank\" without rel=\"noopener\"", check_target_blank_noopener(html_files)),
        ("Dangerous JS sinks", check_js_sinks(js_files)),
        ("Hardcoded secrets", check_secrets(all_files)),
        ("netlify.toml security headers", check_netlify_headers(root)),
        ("Form method/action/honeypot", check_forms(html_files)),
    ]

    total = 0
    for label, problems in checks:
        if problems:
            print(f"\nFAIL — {label}")
            for path, msg in problems:
                print(f"   - {path}: {msg}")
            total += len(problems)
        else:
            print(f"OK   — {label}")

    print(f"\n{total} problem(s) found.")
    sys.exit(1 if total else 0)


if __name__ == "__main__":
    main()