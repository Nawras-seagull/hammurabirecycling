#!/usr/bin/env python3
"""
test_headers_live.py — checks the actual HTTP response headers of a
deployed (or locally served) site. Run this AFTER deploying to a
Netlify preview/production URL, or against `localhost` while running
a local static server.

Standalone: stdlib only (urllib), no dependency on any other test file.

Checks:
  - the page responds with 200
  - an http:// request to the domain redirects to https://
    (skipped automatically when testing localhost)
  - the baseline security headers from netlify.toml are actually being
    sent: X-Frame-Options, X-Content-Type-Options, Referrer-Policy
  - Content-Type is text/html for a page request
  - a known static asset (assets/css/style.css) is served with a
    long-lived Cache-Control header, confirming netlify.toml's caching
    rules took effect

Usage:
    python3 test_headers_live.py https://hammurabirecycling.com
    python3 test_headers_live.py http://localhost:8080
Exit code is non-zero if any check fails.
"""
import argparse
import sys
import urllib.error
import urllib.request


def fetch(url, method="GET"):
    req = urllib.request.Request(url, method=method, headers={"User-Agent": "site-header-test/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, dict(resp.headers), resp.geturl()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers or {}), e.geturl()


def main():
    parser = argparse.ArgumentParser(description="Check live HTTP response headers of a deployed site.")
    parser.add_argument("base_url", help="e.g. https://hammurabirecycling.com or http://localhost:8080")
    args = parser.parse_args()
    base = args.base_url.rstrip("/")
    is_local = "localhost" in base or "127.0.0.1" in base

    problems = []

    # 1. Homepage responds 200
    try:
        status, headers, final_url = fetch(base + "/")
    except Exception as e:
        print(f"FAIL — could not reach {base}/: {e}")
        sys.exit(1)

    if status != 200:
        problems.append(f"GET {base}/ returned status {status}, expected 200")
    else:
        print(f"OK   GET {base}/ → 200")

    # 2. http:// redirects to https:// (skip for localhost, which is fine over plain http)
    if base.startswith("https://") and not is_local:
        http_base = "http://" + base[len("https://"):]
        try:
            status, headers, final_url = fetch(http_base + "/")
            if not final_url.startswith("https://"):
                problems.append(f"{http_base}/ did not redirect to https:// (ended at {final_url})")
            else:
                print(f"OK   {http_base}/ redirects to https://")
        except Exception as e:
            problems.append(f"could not check http:// → https:// redirect: {e}")

    # 3. Security headers on the homepage response
    status, headers, final_url = fetch(base + "/")
    lower_headers = {k.lower(): v for k, v in headers.items()}
    required_headers = {
        "x-frame-options": None,
        "x-content-type-options": "nosniff",
        "referrer-policy": None,
    }
    for header, expected_value in required_headers.items():
        if header not in lower_headers:
            problems.append(f"missing response header: {header}")
        elif expected_value and expected_value.lower() not in lower_headers[header].lower():
            problems.append(f"{header} is \"{lower_headers[header]}\", expected to contain \"{expected_value}\"")
        else:
            print(f"OK   header {header}: {lower_headers[header]}")

    # 4. Content-Type is HTML for a page
    ct = lower_headers.get("content-type", "")
    if "text/html" not in ct.lower():
        problems.append(f"homepage Content-Type is \"{ct}\", expected text/html")
    else:
        print(f"OK   Content-Type: {ct}")

    # 5. Static asset caching
    try:
        status, headers, _ = fetch(base + "/assets/css/style.css")
        lower_asset_headers = {k.lower(): v for k, v in headers.items()}
        cache_control = lower_asset_headers.get("cache-control", "")
        if status != 200:
            problems.append(f"assets/css/style.css returned status {status}")
        elif "max-age" not in cache_control.lower():
            problems.append(f"assets/css/style.css Cache-Control header (\"{cache_control}\") has no max-age — caching rule may not have applied")
        else:
            print(f"OK   assets/css/style.css Cache-Control: {cache_control}")
    except Exception as e:
        problems.append(f"could not fetch assets/css/style.css: {e}")

    print(f"\n{len(problems)} problem(s) found.")
    for p in problems:
        print(f"   - {p}")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()