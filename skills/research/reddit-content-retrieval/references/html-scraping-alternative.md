# Alternative: Direct old.reddit.com HTML Scraping

## When This Works
- When Arctic-Shift doesn't have the subreddit or posts you need
- When you need to search for threads by topic first (discovery phase)
- When the Reddit JSON API returns 403 but HTML pages work

## Technique (Tested: 2026-08)

### Phase 1: Find Thread URLs via Search

```python
import urllib.request
import ssl
import re

ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

def fetch_old_reddit(url, timeout=15):
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0',
    })
    resp = urllib.request.urlopen(req, context=ssl_ctx, timeout=timeout)
    return resp.read().decode('utf-8', errors='replace')

# Search for threads
search_url = "https://old.reddit.com/r/Truckers/search/?q=ELD+complaints&restrict_sr=on&sort=relevance&t=all"
html = fetch_old_reddit(search_url)

# Extract thread URLs from search results
thread_urls = re.findall(r'href="(/r/[^"]+/comments/[a-z0-9]+/[^"]+)"', html)
unique_urls = list(set(thread_urls))[:10]  # Dedupe and limit
```

### Phase 2: Fetch Thread Content

```python
def extract_post_content(html):
    """Extract post/comment text from old.reddit.com HTML"""
    posts = re.findall(r'class="md"[^>]*>(.*?)</div>', html, re.DOTALL)
    cleaned = []
    for p in posts:
        text = re.sub(r'<[^>]+>', ' ', p)
        text = text.replace('&amp;', '&')
        text = text.replace('&#39;', "'")
        text = text.replace('&quot;', '"')
        text = re.sub(r'\s+', ' ', text).strip()
        if len(text) > 50 and 'archived post' not in text.lower():
            cleaned.append(text)
    return cleaned

# Fetch and parse each thread
for url_path in unique_urls[:5]:
    thread_url = f"https://old.reddit.com{url_path}"
    html = fetch_old_reddit(thread_url)
    
    # Get title
    title_match = re.search(r'<title>([^<]+)</title>', html)
    if title_match:
        print(f"Title: {title_match.group(1)}")
    
    # Get posts/comments
    posts = extract_post_content(html)
    for i, post in enumerate(posts[:10]):
        print(f"  [{i+1}] {post[:500]}")
```

## Key Differences from Arctic-Shift

| Aspect | HTML Scraping | Arctic-Shift |
|--------|---------------|--------------|
| Discovery | ✅ Built-in search | ❌ No text search |
| Coverage | ✅ All subreddits | ⚠️ Uneven coverage |
| Freshness | ✅ Real-time | ⚠️ May lag 1+ week |
| Reliability | ⚠️ May get blocked | ✅ Consistent |
| Speed | ⚠️ Multiple requests | ✅ Single API call |

## Pitfalls

1. **Rate limiting**: Don't fetch too many threads too quickly. Add 1-2 second delays between requests.

2. **Archived threads**: Posts older than 6 months show "This is an archived post" — filter these out.

3. **HTML entity decoding**: Must decode `&#39;`, `&amp;`, `&quot;`, etc. manually — Python's `html.unescape()` works too.

4. **Search URL format**: Use `old.reddit.com` not `www.reddit.com`. The `restrict_sr=on` parameter limits to the subreddit.

5. **May get blocked**: This technique worked in testing but Reddit could block it. If you get 403 errors, fall back to Arctic-Shift.

## When NOT to Use

- If you have post IDs already → use Arctic-Shift `/posts/ids`
- If you need comment trees → use Arctic-Shift `/comments/tree`
- If you're making 50+ requests → use Arctic-Shift (less likely to trigger rate limits)
- If the subreddit is well-archived in Arctic-Shift → use Arctic-Shift (faster)

## Example: Industry Research Workflow

```python
# 1. Define search queries
queries = [
    "trucking software complaints",
    "ELD logbook frustrating",
    "freight broker software",
    "fleet management sucks",
]

# 2. For each query, find threads
all_threads = []
for q in queries:
    search_url = f"https://old.reddit.com/r/Truckers/search/?q={q.replace(' ', '+')}&restrict_sr=on&sort=relevance&t=all"
    html = fetch_old_reddit(search_url)
    urls = re.findall(r'href="(/r/[^"]+/comments/[a-z0-9]+/[^"]+)"', html)
    all_threads.extend(urls)

# 3. Dedupe and fetch content
unique = list(set(all_threads))[:20]
for url in unique:
    html = fetch_old_reddit(f"https://old.reddit.com{url}")
    posts = extract_post_content(html)
    # ... analyze posts
```
