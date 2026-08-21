#!/usr/bin/env python3
"""
reddit-digest.py — safe, ban-proof daily Reddit digest (RSS-only, stdlib only).

* No login, no API key, no .json scraping, no browser.
* Fetches each subreddit's PUBLIC .rss feed, pulls top posts by score,
  formats a compact digest, prints to stdout (for Hermes cron -> Telegram).
* Zero external dependencies (urllib + xml only) so it runs in any cron env.

Provenance: method cross-checked with r/hermesagent thread
"How are you getting Hermes to read Reddit reliably?" (post 1trm97s) and
u/HolmeBengt's reddit-reader approach — RSS is the ban-safe path.

EDIT THE SUBS LIST BELOW for your interests.
Override at runtime:  reddit-digest.py sub1 sub2 sub3
"""
import gzip
import re
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

# ---------------- CONFIG (edit me) ----------------
SUBS = [
    "hermesagent",
    "dataengineering",
    "learnpython",
    "Python",
]
TOP_N = 5            # posts per subreddit
DELAY_S = 8          # politeness delay between feeds (avoid 429)
UA = ("Mozilla/5.0 (compatible; hermes-reddit-digest/1.0; "
      "+https://github.com/NousResearch/hermes-agent)")
# --------------------------------------------------

ATOM = "{http://www.w3.org/2005/Atom}"


def fetch(url, tries=4):
    last = None
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": UA,
                "Accept": "application/atom+xml, application/rss+xml, application/xml, text/xml",
                "Accept-Encoding": "identity",  # avoid gzip so stdlib can read it
            })
            with urllib.request.urlopen(req, timeout=20) as r:
                data = r.read()
            if data[:2] == b"\x1f\x8b":  # gzip fallback
                data = gzip.decompress(data)
            return data.decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            last = e
            if e.code == 429:
                wait = DELAY_S * (attempt + 1)  # linear backoff
                time.sleep(wait)
                continue
            raise
    raise last or RuntimeError("fetch failed")


def _num(s):
    s = s.replace(",", "")
    try:
        return int(s)
    except ValueError:
        return 0


def parse_feed(xml, sub):
    root = ET.fromstring(xml)
    out = []
    for e in root.findall(f"{ATOM}entry"):
        title_el = e.find(f"{ATOM}title")
        link_el = e.find(f"{ATOM}link")
        updated_el = e.find(f"{ATOM}updated")
        content_el = e.find(f"{ATOM}content")
        title = (title_el.text or "").strip()
        title = re.sub(r"\s*\(self\.[^)]*\)\s*$", "", title)  # drop (self.x)
        link = link_el.get("href") if link_el is not None else ""
        updated = (updated_el.text or "")[:10] if updated_el is not None else ""
        content = content_el.text or "" if content_el is not None else ""
        m_s = re.search(r"([\d,]+)\s*points?", content, re.I)
        m_c = re.search(r"([\d,]+)\s*comments?", content, re.I)
        out.append({
            "title": title,
            "link": link,
            "updated": updated,
            "score": _num(m_s.group(1)) if m_s else 0,
            "comments": _num(m_c.group(1)) if m_c else 0,
        })
    out.sort(key=lambda x: x["score"], reverse=True)
    return out[:TOP_N]


def main():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines = [f"\U0001F4E1 Reddit Digest \u2014 {today} (UTC)",
             "RSS-only \u00b7 ban-safe \u00b7 no login", ""]
    for sub in SUBS:
        url = f"https://www.reddit.com/r/{sub}/.rss"
        try:
            xml = fetch(url)
            posts = parse_feed(xml, sub)
            lines.append(f"r/{sub} \u2014 top {len(posts)}")
            for i, p in enumerate(posts, 1):
                t = p["title"]
                if len(t) > 90:
                    t = t[:87] + "..."
                lines.append(f"{i}. \U0001F525{p['score']} \U0001F4AC{p['comments']} {t}")
                lines.append(f"   {p['link']}")
            lines.append("")
        except Exception as ex:
            lines.append(f"r/{sub} \u2014 \u26A0 fetch failed: {ex}")
            lines.append("")
        time.sleep(DELAY_S)
    digest = "\n".join(lines)
    if len(digest) > 3900:  # Telegram soft cap
        digest = digest[:3900] + "\n\u2026(truncated)"
    print(digest)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        SUBS = list(sys.argv[1:])
    main()
