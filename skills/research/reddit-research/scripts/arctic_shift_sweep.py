#!/usr/bin/env python3
"""Multi-subreddit sweep via Arctic-Shift with error visibility (stdlib only).

Why this exists: the smart search script (~/.hermes/scripts/reddit_search.py) is
NOT present on every box. This is a drop-in for the sweep half of that workflow.

Verified Arctic-Shift quirks (2026-08, datacenter IP):
  - limit=200 -> HTTP 400 Bad Request on many subreddits; keep limit<=100 and
    paginate with after=<last post id> when you need more.
  - Some subreddits (e.g. cscareerquestions) -> HTTP 422 Unprocessable Entity,
    permanently unservable; mark unsupported, don't retry in a loop.
  - Rate-limit body: {"data": null, "error": "Timeout. Maybe slow down a bit"}
  - Success shape: {"data": [...]}. ALWAYS check for the "error" key before
    treating a response as "subreddit has no posts".

Usage:
  python3 arctic_shift_sweep.py hermesagent AI_Agents --limit 100 \
      --kw "job|intern|portfolio" --out /opt/work/reddit_hits.json
  python3 arctic_shift_sweep.py hermesagent --comments 5   # fetch top-5 posts' comments too

Output: JSON dict subreddit -> list of post dicts (or {"error": ...} per sub).
"""
import argparse, json, re, time, urllib.request, urllib.parse

BASE = "https://arctic-shift.photon-reddit.com/api"


def fetch(url, retries=6, timeout=90):
    last = ""
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode())
        except Exception as e:
            last = str(e)
            time.sleep(5 + 5 * i)  # backs off to ~30s; API rate-limits hard
    return {"error": last}


def sweep_posts(sub, limit=100):
    d = fetch(f"{BASE}/posts/search?subreddit={sub}&limit={limit}")
    if "error" in d:
        return None, d["error"]
    return d.get("data") or [], None


def get_comments(post_id, limit=100):
    d = fetch(f"{BASE}/comments/search?link_id={post_id}&limit={limit}")
    if "error" in d:
        return None, d["error"]
    return d.get("data") or [], None


def main():
    ap = argparse.ArgumentParser(description="Arctic-Shift subreddit sweep")
    ap.add_argument("subreddits", nargs="+")
    ap.add_argument("--limit", type=int, default=100, help="max 100 (larger 400s)")
    ap.add_argument("--kw", default="", help="optional regex; posts must match title/selftext")
    ap.add_argument("--comments", type=int, default=0, help="fetch comments for top N posts by score")
    ap.add_argument("--out", default="/opt/work/reddit_sweep.json")
    args = ap.parse_args()

    kw = re.compile(args.kw, re.I) if args.kw else None
    out = {}
    for sub in args.subreddits:
        posts, err = sweep_posts(sub, args.limit)
        if err:
            print(f"== {sub}: ERROR {err}", flush=True)
            out[sub] = {"error": err}
            time.sleep(6)
            continue
        keep = posts
        if kw:
            keep = [p for p in posts if kw.search((p.get("title") or "") + " " + (p.get("selftext") or "")[:1500])]
        if args.comments:
            top = sorted(keep, key=lambda p: p.get("score") or 0, reverse=True)[: args.comments]
            for p in top:
                cs, cerr = get_comments(p["id"])
                p["_comments"] = [{"author": c.get("author"), "score": c.get("score"),
                                   "body": (c.get("body") or "")[:500]} for c in (cs or [])]
                if cerr:
                    p["_comments_error"] = cerr
                time.sleep(5)
        out[sub] = [{"id": p["id"], "title": p.get("title"), "score": p.get("score"),
                     "num_comments": p.get("num_comments"), "url": p.get("url"),
                     "created_utc": p.get("created_utc"), "author": p.get("author"),
                     "selftext": (p.get("selftext") or "")[:600],
                     **({"_comments": p["_comments"]} if "_comments" in p else {})} for p in keep]
        print(f"== {sub}: {len(posts)} scanned -> {len(keep)} kept", flush=True)
        time.sleep(6)

    with open(args.out, "w") as f:
        json.dump(out, f, indent=1)
    print(f"saved {args.out}")


if __name__ == "__main__":
    main()
