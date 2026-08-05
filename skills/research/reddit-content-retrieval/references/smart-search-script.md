# Smart Reddit Search Script

Combined DuckDuckGo + Arctic-Shift search script. Handles text search (which Arctic-Shift can't do natively).

## Location
`~/.hermes/scripts/reddit_search.py`

## Usage
```bash
# Search across subreddits
python3 ~/.hermes/scripts/reddit_search.py "best youtube bodyweight workout" --subreddits Fitness,bodyweightfitness,loseit

# Fetch full post + comments by ID
python3 ~/.hermes/scripts/reddit_search.py --post 1urrb6u

# Default subreddits (if --subreddits not specified)
bodyweightfitness, Fitness, loseit, HomeWorkout, progresspics, gainit
```

## How it works
1. **DuckDuckGo lite** — searches `site:reddit.com` for matching URLs, extracts post IDs
2. **Arctic-Shift** — pulls recent posts from specified subreddits (no text search)
3. **Keyword filter** — filters Arctic-Shift results by keywords in title+body
4. Deduplicates by post ID across both sources

## Limitations
- DuckDuckGo lite sometimes shows bot challenges (retry after seconds)
- Arctic-Shift text search is broken — only subreddit-filtered pulls work
- Arctic-Shift coverage is uneven for fitness subreddits
- No API keys needed for basic operation
