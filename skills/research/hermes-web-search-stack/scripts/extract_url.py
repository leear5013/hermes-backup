#!/usr/bin/env python3
"""Fetch + extract readable text from a URL using trafilatura, falling back to scrapling.

Usage:
    /opt/venv/bin/python extract_url.py <url> [max_chars]

Layers tried in order:
    1. trafilatura.fetch_url + extract (clean text, no browser)
    2. scrapling Fetcher.get (curl_cffi stealth) + get_all_text
    3. requests + trafilatura.extract on raw HTML

Exit code 0 = text extracted, 1 = all layers failed.
"""
import sys

sys.path.insert(0, "/opt/hermes-agent")

MAX_CHARS = int(sys.argv[2]) if len(sys.argv) > 2 else 20000


def layer1(url: str):
    import trafilatura
    downloaded = trafilatura.fetch_url(url)
    if downloaded:
        text = trafilatura.extract(downloaded, include_comments=False, include_tables=False)
        if text and len(text.strip()) > 200:
            return text
    return None


def layer2(url: str):
    from scrapling import Fetcher
    page = Fetcher.get(url, headless=False)
    if page.status == 200:
        text = page.get_all_text(max_chars=MAX_CHARS)
        if text and len(text.strip()) > 200:
            return text
    return None


def layer3(url: str):
    import requests, trafilatura
    r = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"})
    if r.status_code == 200 and "verifying your browser" not in r.text[:2000].lower():
        text = trafilatura.extract(r.text, include_comments=False, include_tables=False)
        if text and len(text.strip()) > 200:
            return text
    return None


def main():
    if len(sys.argv) < 2:
        print("usage: extract_url.py <url> [max_chars]", file=sys.stderr)
        sys.exit(1)
    url = sys.argv[1]
    for i, layer in enumerate((layer1, layer2, layer3), 1):
        try:
            text = layer(url)
            if text:
                print(f"# layer{i}: {len(text)} chars")
                print(text[:MAX_CHARS])
                sys.exit(0)
            print(f"# layer{i}: no usable text", file=sys.stderr)
        except Exception as e:
            print(f"# layer{i}: {type(e).__name__}: {e}", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
