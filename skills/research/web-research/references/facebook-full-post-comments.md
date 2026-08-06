# Facebook Full Post + Comments (no login, verified 2026-08)

When the user needs the FULL post text AND comments (not just the og:description preview),
the Googlebot user-agent trick on the ORIGINAL post URL returns everything: complete post
body, all visible comments with author names, reply counts, reaction/share counts.

## The Main Route: Googlebot UA on the original post URL

```bash
# First, get the original post URL from the share link (see facebook-share-link.md):
#   fetch https://www.facebook.com/share/p/<share_id>/ with a mobile UA,
#   read og:url -> e.g. https://www.facebook.com/ahmedezatacc/posts/10164485092669663/

# Then fetch the ORIGINAL POST URL with a GOOGLEBOT UA:
curl -sL -A "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)" \
  --max-time 20 "https://www.facebook.com/ahmedezatacc/posts/10164485092669663/" -o post.html
# -> returns ~1MB HTML: NO login wall, full post + comments embedded
```

Key insight: Facebook serves a full public rendering to Googlebot (it must, for SEO).
The page contains no "Log into Facebook" wall — it's a real public snapshot.

## Extract Visible Text (post + comments in order)

```bash
python3 << 'PYEOF'
import re, html as htmlmod

content = open('post.html', encoding='utf-8', errors='ignore').read()

# Strip scripts/styles, then tags
content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.S)
content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.S)
text = re.sub(r'<[^>]+>', '\n', content)
text = htmlmod.unescape(text)
lines = [l.strip() for l in text.split('\n') if l.strip() and len(l.strip()) > 2]

# Post body = lines between the author line and "All reactions:"
# Comments start after "Most relevant" — author name line precedes each comment body
for l in lines:
    print(l[:300])
PYEOF
```

## Extract Comments from JSON (cleaner — gets exact comment bodies)

Facebook embeds comments as JSON blobs. Pattern: `"body":{"text":"..."}`.

```python
import re, json

comments = re.findall(r'"body":\s*\{"text":\s*"((?:[^"\\]|\\.)*)"', content)
for c in comments:
    try:
        c = json.loads('"' + c + '"')  # proper unescaping incl. \/ and unicode
        c = c.encode('utf-8', errors='ignore').decode('utf-8', errors='ignore')  # drop surrogates
        print(c)
    except Exception:
        pass
```

Notes:
- Duplicates appear (same comment twice in different JSON blobs) — dedupe with a set.
- Authors are visible in the text-extraction pass (name line directly above each comment).
- Reply counts appear as "N Replies"; reactions appear as "All reactions: N".
- Surrogate pairs (emoji like 😄) break naive `unicode_escape` decoding — use
  `json.loads('"' + s + '"')` then drop surrogates, NOT `.decode('unicode_escape')`.

## Alternative: Embed Plugin (full post text, no comments)

```bash
# Works without login; returns FULL post body (not truncated like og:description).
# Needs JS rendering -> use Chromium headless:
chromium --headless --no-sandbox --disable-gpu --dump-dom \
  "https://www.facebook.com/plugins/post.php?href=<URL_ENCODED_POST_URL>&show_text=true&width=500" \
  2>/dev/null > embed.html
```

- Returns ~74KB DOM with the complete post text in Arabic/any script.
- `show_comments=true` does NOT add comments (still post text only).
- Good fallback when Googlebot UA fails; post text here is NOT truncated (unlike og:description).

## Route Comparison

| Route | Post text | Comments | Login? |
|---|---|---|---|
| Googlebot UA on post URL | ✅ FULL | ✅ ALL visible + authors | No |
| `/share/p/<id>/` og:description | ⚠️ ~50-60 words truncated | ❌ | No |
| Embed plugin (Chromium) | ✅ FULL | ❌ | No |
| mbasic / m.facebook.com | ❌ title only | ❌ | Login wall |

## Workflow

1. Share link → fetch `/share/p/<id>/` (mobile UA) → get `og:url` (original post URL)
2. Fetch original post URL with Googlebot UA → full post + comments
3. Text-extract for ordered reading; JSON-extract `"body":{"text":...}` for clean comment list
4. If Googlebot route fails, fall back to embed plugin for full post text only
