# Facebook Share-Link Retrieval (no login, verified 2026-08)

Recipe for extracting post content from a Facebook share link like
`https://www.facebook.com/share/18vJ6uMZaE/?mibextid=wwXIfr` — no login, no cookies, works from a server IP.

## The One Working Route

```bash
curl -sL -A "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1" \
  --max-time 20 "https://www.facebook.com/share/p/<share_id>/" -o page.html
```

Key detail: insert `/p/` between `share` and the ID. The bare `/share/<id>/` URL returns an error page.
Returns ~328KB HTML. The post text lives in the `og:description` meta tag, hex-entity-encoded.

## Extract + Decode

```python
import re

content = open('page.html', encoding='utf-8', errors='ignore').read()

# Post text (Arabic/any script) — hex entities
raw = re.search(r'property="og:description" content="([^"]*)"', content).group(1)
decoded = re.sub(r'&#x([0-9a-fA-F]+);', lambda m: chr(int(m.group(1), 16)), raw)
# -> 'في فرصه كبيره في السوق العربي ممكن تحققلك الاف الدولارات لو استغليتها صح ….  في تول اسمها Groups Watcher...'

# Author name
author = re.search(r'property="og:title" content="([^"]*)"', content).group(1)

# Original post URL (contains percent-encoded full title — decode with urllib.parse.unquote)
url = htmlmod.unescape(re.search(r'property="og:url" content="([^"]*)"', content).group(1))
# -> https://www.facebook.com/ahmedezatacc/posts/في-فرصه-...-/10164485092669663/

# Post type
post_type = re.search(r'property="og:type" content="([^"]*)"', content).group(1)  # 'video.other' = video post

# Media
image = re.search(r'property="og:image" content="([^"]*)"', content).group(1)
```

Note: `html.unescape()` alone does NOT decode `&#x...;` hex entities in some Python versions —
the manual `re.sub` with `chr(int(..., 16))` is the reliable path. (In this session `htmlmod.unescape()`
returned empty for the description; the manual decoder worked.)

## What Each URL Variant Returns

| URL variant | Result |
|---|---|
| `facebook.com/share/<id>/` | 1.5KB "Sorry, something went wrong" error page |
| `facebook.com/share/p/<id>/` | **~328KB — og:description with full post text** ✅ |
| `mbasic.facebook.com/share/<id>/` | 255KB login wall ("Log into Facebook") |
| `m.facebook.com/share/<id>/` | 13KB — page title only, no body |
| `facebook.com/<author>/posts/<id>/` | title only, ~50-word public preview |

## Limits

- `og:description` here is truncated (~50-60 words) — this route gives ONLY the preview.
- For the FULL post + comments, do NOT assume login is required: fetch the original post
  URL (from `og:url`) with a **Googlebot UA** — see `facebook-full-post-comments.md`.
- Author pages (`facebook.com/<author>`) are login-walled with a normal UA; the share-link
  route and the Googlebot UA route are the anonymous paths.
- Works for text + video posts; image posts presumably same pattern (og:type will differ).

## Cross-checking via the original post URL

The `og:url` gives `facebook.com/<handle>/posts/<post_id>/` which reveals the post ID —
useful for searching the same content elsewhere (Google, other platforms) even when FB itself is walled.
