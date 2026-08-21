#!/usr/bin/env python3
"""
reddit-top.py — find the highest-reach posts in a subreddit over a time window.

One command. No login. No ban risk. Stdlib-only.

Usage:
  python3 reddit-top.py                       # r/hermesagent, last 48h, top 5
  python3 reddit-top.py dataengineering 72 10 # other sub, 72h, top 10

Pipeline (each step encodes a wall we hit so you don't have to):
  1. DISCOVERY via public RSS (.rss)        -> reddit .json is 403-dead
  2. REACH via ArcticShift mirror comments  -> RSS hides scores entirely;
                                               ArcticShift post scores are
                                               ingest-time snapshots (useless
                                               for fresh posts); PullPush is
                                               429-limited + dated archive.
     Comment volume = truest reach signal available safely.
  3. PAGINATION via before=<oldest_ts>      -> API caps at limit=100 silently;
                                               without this you undercount big
                                               threads (138-comment post reads
                                               as 100).
"""
import gzip
import json
import re
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

UA = {"User-Agent": "Mozilla/5.0 (compatible; hermes-reddit-top/1.0)",
      "Accept-Encoding": "identity"}
ATOM = "{http://www.w3.org/2005/Atom}"
ARCTIC = "https://arctic-shift.photon-reddit.com/api"
PAGE_SLEEP = 0.8   # politeness between mirror pages
POST_SLEEP = 1.0   # politeness between posts


def http_get(url, tries=3, backoff=5):
    last = None
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=25) as r:
                data = r.read()
            if data[:2] == b"\x1f\x8b":
                data = gzip.decompress(data)
            return data
        except Exception as e:  # noqa: BLE001 - report, don't loop forever
            last = e
            time.sleep(backoff * (attempt + 1))
    raise last


# ---------- Step 1: discovery via RSS ----------
def discover(sub, hours):
    xml = http_get(f"https://www.reddit.com/r/{sub}/.rss").decode("utf-8", "replace")
    root = ET.fromstring(xml)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    posts = []
    for e in root.findall(f"{ATOM}entry"):
        upd = e.find(f"{ATOM}updated").text
        dt = datetime.fromisoformat(upd.replace("Z", "+00:00"))
        link = e.find(f"{ATOM}link").get("href")
        title = re.sub(r"\s*\(self\.[^)]*\)\s*$", "",
                       e.find(f"{ATOM}title").text.strip())
        m = re.search(r"/comments/(\w+)/", link)  # permalink, NOT post-id attr
        if dt >= cutoff and m:
            posts.append({"id": m.group(1), "title": title,
                          "url": link, "when": upd})
    return posts


# ---------- Step 2+3: true comment counts via ArcticShift ----------
def count_comments(pid):
    total, before = 0, None
    for _ in range(20):  # hard page cap: never loop forever
        url = f"{ARCTIC}/comments/search?link_id={pid}&limit=100"
        if before:
            url += f"&before={before}"
        batch = json.loads(http_get(url)).get("data", [])
        if not batch:
            break
        total += len(batch)
        oldest = min(int(c.get("created_utc", 0)) for c in batch)
        if len(batch) < 100 or oldest == before:
            break
        before = oldest
        time.sleep(PAGE_SLEEP)
    return total


def main():
    sub = sys.argv[1] if len(sys.argv) > 1 else "hermesagent"
    hours = int(sys.argv[2]) if len(sys.argv) > 2 else 48
    top_n = int(sys.argv[3]) if len(sys.argv) > 3 else 5

    print(f"Discovering r/{sub} posts from the last {hours}h via RSS ...")
    try:
        posts = discover(sub, hours)
    except Exception as e:  # noqa: BLE001
        print(f"WALL HIT: RSS discovery failed ({e}). "
              f"Reddit may be rate-limiting this IP; wait or reduce frequency.")
        sys.exit(1)
    if not posts:
        print("No posts found in that window.")
        sys.exit(0)
    print(f"Found {len(posts)} posts. Counting real comment totals "
          f"(ArcticShift mirror, paginated) ...\n")

    rows = []
    for p in posts:
        try:
            n = count_comments(p["id"])
        except Exception:  # noqa: BLE001
            n = -1
        p["comments"] = n
        rows.append(p)
        label = f"{n} comments" if n >= 0 else "count failed (mirror hiccup)"
        print(f"  {label:>28} | {p['title'][:55]}")
        time.sleep(POST_SLEEP)

    ok = sorted((r for r in rows if r["comments"] >= 0),
                key=lambda x: x["comments"], reverse=True)[:top_n]

    print(f"\n=== TOP {min(top_n, len(ok))} by reach — r/{sub}, last {hours}h ===")
    for i, r in enumerate(ok, 1):
        print(f"{i}. [{r['comments']} comments] {r['title']}")
        print(f"   {r['url']}")


if __name__ == "__main__":
    main()
