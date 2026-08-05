# Worked example: fetching r/hermesagent post 1urrb6u (2026-08-04)

## Goal
Retrieve the body of a Reddit post shared via `https://www.reddit.com/r/hermesagent/s/<id>` (share-shortlink) with comment ID `1urrb6u`.

## Failure chain (all blocked — do not repeat blindly)
| Route | Result |
|---|---|
| `reddit.com/r/.../comments/1urrb6u.json` | HTML bot-check (403) |
| `old.reddit.com/.../comments/1urrb6u.json` | HTML bot-check |
| `api.reddit.com/...` / `oauth.reddit.com/comments/1urrb6u` | 403 HTML |
| redlib instances (perennialte, privacyredirect, catsarch, artemislena, nadeko, r4fo, cow.rip, privadency, dns4all, private.coffee) | Anubis/Gandalf/Cloudflare challenge pages |
| `reddit.nerdvpn.de` | "Gandalf is checking your connection" |
| `api.allorigins.win/raw?url=...` | 522 |
| `api.codetabs.com/v1/proxy?quest=...` | 521 |
| `r.jina.ai/<reddit url>` | "blocked by network security" |
| `webcache.googleusercontent.com` | 302 (gone) |
| Wayback CDX + replay (`web/20260710060401/...`) | index lists snapshot but body is just the verification wall |

## Working route (Arctic-Shift archive)
```python
import json, urllib.request
# by post ID
req = urllib.request.Request(
    "https://arctic-shift.photon-reddit.com/api/posts/ids?ids=1urrb6u")
d = json.load(urllib.request.urlopen(req, timeout=60))
p = d["data"][0]
print(p["title"], "|", p["author"])          # "This Simple SOUL.md Tweak..." | NinjaAlaska
print(p["selftext"])                          # full body (contained the SOUL.md content)
```
- Endpoint returned 200 on first try; `selftext` held the full content.
- Also seen working: `https://arctic-shift.photon-reddit.com/api/posts/search?subreddit=hermesagent&limit=40` (171KB of recent posts).

## Lesson
When asked to use/copy content from a Reddit post, go straight to Arctic-Shift by the comment ID rather than exhausting Reddit mirrors/proxies first. The permalink path `/comments/<ID>/` yields the ID directly; strip a leading `t3_` prefix if present.

## Caveat
Arctic-Shift is a third-party Pushshift-style archive. Verify the extracted `selftext` is genuinely from the target post (`id` field matches) before treating it as authoritative.