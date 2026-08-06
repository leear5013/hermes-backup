# Reddit Consensus Research — Methodology

## Multi-Source Pipeline

```
User Query
    │
    ▼
Search Planner (Hermes)
    │
    ├──────────────┐
    ▼              ▼
DuckDuckGo      Arctic-Shift
HTML search      subreddit pull
    │              │
    └──────┬───────┘
           ▼
Client-side keyword filter
           │
           ▼
Fetch top posts by ID
           │
           ▼
Fetch comments via /comments/tree
           │
           ▼
Unwrap item["data"] nesting
           │
           ▼
Score & cluster by stance
           │
           ▼
LLM consensus report
```

## Discovery Phase

Use `site:reddit.com/r/<subreddit>` queries via DuckDuckGo **HTML** (not lite):
```
site:reddit.com/r/hermesagent deploy hosting
site:reddit.com/r/selfhosted hermes agent
```

**CRITICAL:** DuckDuckGo `html.duckduckgo.com` works from datacenter IPs.
DuckDuckGo `lite.duckduckgo.com` is BLOCKED (bot challenges).

## Content Extraction Priority

1. **Arctic-Shift `/posts/ids?ids=X`** — fastest, most reliable
2. **Arctic-Shift `/comments/tree?link_id=X&limit=100`** — full comment threads
3. **Arctic-Shift `/posts/search?subreddit=X&limit=100`** — recent posts (no text search)
4. **Reddit JSON** — blocked from datacenter IPs
5. **Jina Reader** — blocked by Reddit bot detection

## Arctic-Shift Comment Nesting (CRITICAL)

The `/comments/tree` endpoint returns comments NESTED inside `item["data"]`:
```json
{"data": [{"kind": "t1", "data": {"author": "...", "body": "...", "score": ...}}]}
```
Access `item["data"]["author"]`, NOT `item["author"]` — the latter gives empty strings.

## Short Link Resolution

Reddit `/s/xxx` short links → resolve to post ID:
```python
r = subprocess.run(["curl", "-sL", "-o", "/dev/null", "-w", "%{url_effective}", url])
post_id = re.search(r'/comments/(\w+)/', r.stdout).group(1)
```

## Comment Scoring

Weight: `log(upvotes + 1)` × author_reputation × depth × recency

## Opinion Clustering

Group by: topic keywords, sentiment, stance, expertise signals

## Output Format

```markdown
## Consensus Report: [Topic]

### Majority Opinion (high-confidence)
### Minority Opinion
### Common Complaints
### Common Praise
### Alternatives Mentioned
### Representative Quotes
```

## Verified Working Code (from live session 2026-08-06)

### Phase 1: Discovery via DuckDuckGo HTML
```python
# html.duckduckgo.com works from datacenter IPs — lite.duckduckgo.com is BLOCKED
url = f"https://html.duckduckgo.com/html/?q=site%3Areddit.com+{encoded_query}"
# Extract: <a class="result__a" href="...">title</a> blocks
# DDG wraps URLs in redirects — extract actual reddit URL with regex
```

### Phase 2: Arctic-Shift subreddit pull + client-side filter
```python
# Arctic-Shift text search (q=) is BROKEN — pull all posts, filter locally
url = f"{ARCTIC_BASE}/posts/search?subreddit={sub}&limit=100"
# Filter: keyword_match = any(k in (title + selftext).lower() for k in keywords)
```

### Phase 3: Fetch posts + comments
```python
# Post by ID
url = f"{ARCTIC_BASE}/posts/ids?ids={post_id}"

# Comments — CRITICAL: use /comments/tree, NOT /comments/search
url = f"{ARCTIC_BASE}/comments/tree?link_id={post_id}&limit=100"

# Comment data is NESTED — must unwrap item["data"]
for item in response["data"]:
    if isinstance(item, dict) and "data" in item:
        c = item["data"]
        print(c["author"], c["score"], c["body"])
```

### Full pipeline example (tested 2026-08-06)
Successfully researched "Hermes Agent free hosting options" across r/hermesagent, r/oraclecloud, r/selfhosted, r/homelab — fetched 400+ posts, filtered to 226 deployment-related, fetched 12 posts with 200+ comments, produced weighted consensus report.
