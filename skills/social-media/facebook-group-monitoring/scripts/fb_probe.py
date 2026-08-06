#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fb_probe.py — Facebook reachability probe. Run FIRST whenever FB fetching fails.

Distinguishes a datacenter-IP block from bad cookies in ~10 seconds, so you
never waste time re-copying cookies for an IP problem.

Usage:
    python3 fb_probe.py                  # no cookies: pure IP test
    python3 fb_probe.py config.local.json  # optional: cookie string read from JSON

Verdicts:
    IP BLOCKED      -> datacenter/cloud IP refused by Facebook (even public
                       pages 400 / mbasic returns title "Error"). Cookies are
                       irrelevant from this machine; run on a residential IP.
    IP OK, SESSION? -> the public page works; cookies (or a login) are the
                       next question.
"""
import json
import re
import sys
import urllib.request

MOBILE_UA = ("Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36 "
             "(KHTML, like Gecko) Chrome/120.0 Mobile Safari/537.36")
DESKTOP_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")


def fetch(url, cookie=None, ua=DESKTOP_UA, timeout=25):
    headers = {"User-Agent": ua, "Accept-Language": "ar-EG,ar;q=0.9,en;q=0.5"}
    if cookie:
        headers["Cookie"] = cookie
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", errors="ignore")
    except Exception as e:
        return None, str(e)


def title(html):
    m = re.search(r"<title>(.*?)</title>", html, re.S)
    return m.group(1).strip()[:50] if m else "?"


def main():
    cookie = None
    if len(sys.argv) > 1:
        try:
            cookie = json.load(open(sys.argv[1])).get("cookie_string", "")
            print(f"[info] cookie string loaded ({len(cookie)} chars)")
        except Exception as e:
            print(f"[warn] could not read {sys.argv[1]}: {e}")

    print("\n== 1) public login page (no cookies) — the IP test ==")
    status, body = fetch("https://www.facebook.com/login.php")
    if status == 200:
        print(f"  login.php -> HTTP 200 (OK)  | title='{title(body)}'")
    else:
        print(f"  login.php -> FAILED: {status} {str(body)[:80]}")
        print("\nVERDICT: IP BLOCKED — Facebook refuses this machine's IP "
              "(datacenter/cloud). Cookies are irrelevant here; run the "
              "watcher from a residential IP (customer's machine/browser).")
        return

    print("\n== 2) mbasic with cookies (session sanity) ==")
    status, body = fetch("https://mbasic.facebook.com/", cookie)
    t = title(body)
    if status == 200:
        print(f"  mbasic -> HTTP 200 | {len(body)} bytes | title='{t}'")
        if t.lower() in ("error", "خطأ"):
            print("  -> generic Error page: session refused or IP limited on mbasic")
        elif "Log into Facebook" in body or "login" in body[:3000].lower():
            print("  -> login wall: cookies not accepted/expired")
        else:
            print("  -> logged-in view OK")
    else:
        print(f"  mbasic -> FAILED: {status} {str(body)[:80]}")

    print("\n== 3) mbasic WITHOUT cookies (logged-out baseline) ==")
    status, body = fetch("https://mbasic.facebook.com/")
    if status == 200:
        print(f"  mbasic -> HTTP 200 | {len(body)} bytes | title='{title(body)}'")
    else:
        print(f"  mbasic -> FAILED: {status} {str(body)[:80]}")

    print("\n== 4) optional: private-group check via r.jina.ai (any IP) ==")
    print("  try: curl -s https://r.jina.ai/https://www.facebook.com/groups/<id>/")
    print("  login page => private group | real posts => public group\n")

    print("VERDICT: public pages reachable => IP is NOT fully blocked. If mbasic "
          "still shows 'Error', the session/cookies are the problem (refresh "
          "cookies, ~monthly expiry).")


if __name__ == "__main__":
    main()
