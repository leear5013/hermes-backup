#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fb_probe.py — Facebook reachability diagnostic.
Run FIRST when Facebook fetching fails. Distinguishes:
  IP BLOCK (datacenter IP)  vs  COOKIE PROBLEM  vs  PRIVATE GROUP

Usage:
  python3 fb_probe.py                 # no cookies — tests IP block only
  python3 fb_probe.py "cookie_string" # with cookies — tests session too
  python3 fb_probe.py "cookie_string" https://mbasic.facebook.com/groups/<id>/

Interpretation:
  - www/login.php returns HTTP 400 (even logged out)          -> IP BLOCKED
  - mbasic <title> is 'Error'/'خطأ' everywhere (even home)    -> IP BLOCKED
  - logged-out 400 BUT mbasic-with-cookies shows real content -> cookies OK,
    run from THIS machine. If you're on a cloud VM, this combination is
    impossible — Facebook blocks the IP first.
  - r.jina.ai/<fb-url> returns the login page for a group     -> group is PRIVATE
  - r.jina.ai/<fb-url> returns post content                   -> group is PUBLIC
"""
import json
import re
import sys
import urllib.request

MOBILE_UA = ("Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36 "
             "(KHTML, like Gecko) Chrome/120.0 Mobile Safari/537.36")
DESKTOP_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")


def probe(url, ck=None, ua=DESKTOP_UA, timeout=25):
    headers = {"User-Agent": ua, "Accept-Language": "ar-EG,ar;q=0.9,en;q=0.5"}
    if ck:
        headers["Cookie"] = ck
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            html = r.read().decode("utf-8", errors="ignore")
        t = re.search(r"<title>(.*?)</title>", html, re.S)
        title = t.group(1).strip()[:50] if t else "?"
        return f"200 | {len(html):>7}B | title='{title}'"
    except Exception as e:
        return f"ERR {e}"


def main():
    ck = sys.argv[1] if len(sys.argv) > 1 else None
    target = sys.argv[2] if len(sys.argv) > 2 else None

    print("=== FB reachability probe ===")
    print(f"cookies: {'provided (' + str(len(ck)) + ' chars)' if ck else 'NONE (IP test only)'}")
    print()
    print("1) public login page, www, no cookie :", probe("https://www.facebook.com/login.php"))
    print("2) public login page, www, +cookie   :", probe("https://www.facebook.com/login.php", ck))
    print("3) mbasic home, no cookie            :", probe("https://mbasic.facebook.com/login/"))
    print("4) mbasic home, +cookie, mobile UA   :", probe("https://mbasic.facebook.com/", ck, MOBILE_UA))
    if target:
        print(f"5) target {target} (mbasic, +cookie)  :", probe(target, ck, MOBILE_UA))
    print()
    print("RULES:")
    print("  - 1 fails with 400 -> datacenter IP is BLOCKED. Stop debugging cookies;")
    print("    run the watcher on a residential IP (customer's home machine).")
    print("  - 1 OK but 2 fails -> cookies invalid/expired, re-copy them.")
    print("  - 3/4 title='Error'/'خطأ' -> also an IP-level block on mbasic.")
