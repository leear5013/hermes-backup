#!/usr/bin/env python3
"""Fetch and extract the full body of a Reddit post via Reddit's own RSS endpoint.

Primary method for reading Reddit post text when www/old.reddit.com .json is
bot-blocked (403 / Cloudflare "Just a moment..."). Retries through Reddit's
known intermittent rate-limiting (empty responses).

Usage:
    python3 fetch_reddit_rss.py <post_url_or_id> [subreddit]

    <post_url_or_id>  e.g. "1urrb6u", "https://www.reddit.com/r/hermesagent/comments/1urrb6u/"
    [subreddit]       optional, used only if the ID is passed without a full URL.
                      If omitted with a bare ID, attempts r/<id> which will fail;
                      pass the subreddit from the permalink.

Prints the feed <title> and the extracted post body markdown; if the post embeds
a code block (<pre><code>), also prints that (the verbatim pasted file).

Requires only the Python stdlib (urllib + html). No external deps.
"""
import html as h
import re
import sys
import time
import urllib.parse
import urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")


def fetch(url: str, attempts: int = 6, sleep: float = 5.0) -> str:
    """GET url; retry on empty/intermittent responses (Reddit RSS rate-limits
    by returning an empty body, not an error)."""
    for i in range(attempts):
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=40) as resp:
                raw = resp.read()
        except Exception as e:  # noqa: BLE001 - log and retry transient errors
            print(f"[attempt {i+1}/{attempts}] error: {e}", file=sys.stderr)
            time.sleep(sleep)
            continue
        if not raw:
            print(f"[attempt {i+1}/{attempts}] empty response (rate-limit) - retrying",
                  file=sys.stderr)
            time.sleep(sleep)
            continue
        return raw.decode("utf-8", errors="replace")
    raise RuntimeError("All attempts returned empty/errored responses")


def extract(rss: str) -> tuple[str | None, str | None, str | None]:
    """Return (title, post_body_markdown, code_block)."""
    t = re.search(r"<title[^>]*>(.*?)</title>", rss, re.S)
    title = h.unescape(t.group(1)).strip() if t else None

    m = re.search(r"<content[^>]*>(.*?)</content>", rss, re.S)
    if not m:
        return title, None, None
    html_body = h.unescape(m.group(1))

    # verbatim pasted file lives in <pre><code>...</code></pre>
    code_m = re.search(r"<pre><code>(.*?)</code></pre>", html_body, re.S)
    code = h.unescape(code_m.group(1)).strip() if code_m else None

    # strip block tags to reconstruct post markdown
    body = re.sub(r"<[^>]+>", "", html_body)
    body = h.unescape(body).strip()
    return title, body, code


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    target = sys.argv[1]
    sub = sys.argv[2] if len(sys.argv) > 2 else None

    post_id = re.search(r"/comments/([a-z0-9]+)", target)
    if post_id:
        pid = post_id.group(1)
        sub = sub or (re.search(r"/r/([^/]+)", target).group(1) if "/r/" in target else None)
    else:
        pid = target.strip().lstrip("t3_")
    if not sub:
        print("ERROR: pass the subreddit (bare ID needs it): "
              "python3 fetch_reddit_rss.py <id> <subreddit>", file=sys.stderr)
        return 1

    url = f"https://www.reddit.com/r/{sub}/comments/{pid}/.rss"
    print(f"Fetching {url}", file=sys.stderr)
    rss = fetch(url)

    title, body, code = extract(rss)
    print(f"TITLE: {title}\n")
    if body:
        print("=== POST BODY ===\n")
        print(body)
    if code:
        print("\n\n=== VERBATIM CODE BLOCK (pasted file) ===\n")
        print(code)
        print("\n=== END CODE BLOCK ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())