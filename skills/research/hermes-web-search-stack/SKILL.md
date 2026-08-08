---
name: hermes-web-search-stack
description: Fix Hermes web_search + extract on a VPS (ddgs, scrapling).
---

# Hermes Web Search & Extract Stack (VPS-tested)

Gives Hermes Agent live web search + page extraction on a constrained VPS (Railway/Docker, 500MB disk, no Docker-in-Docker). Verified working 2026-08-08 from a datacenter IP.

## When to use
- User's `web_search`/`web_extract` tools are missing, error "No web search provider configured", or `Registered providers: []`.
- You need to search the web from Hermes (especially `site:reddit.com` discovery for the user's signature research pipeline).
- You need to fetch/extract readable text from a URL that plain requests gets 403'd on (Cloudflare etc.).

## The three-layer root cause (know this before debugging)
1. **No provider configured** → `web.search_backend` unset. Fix: `hermes config set web.search_backend ddgs`.
2. **Package installed in the WRONG interpreter.** The gateway runs `/opt/venv/bin/python` (NOT system `python3`). `pip show ddgs` with system python says installed → gateway still fails `import ddgs` → provider `is_available() == False`. Always check/install with `/opt/venv/bin/pip`.
3. **"Plugins don't load" is a test artifact.** Plugin discovery is LAZY — `get_plugin_manager()` does NOT auto-discover. You must call `pm.discover_and_load()` (or in tools: `_ensure_web_plugins_loaded()` runs at every web_search dispatch). A fresh venv probe that skips discovery will print `Registered providers: []` and look broken.

## The fix chain (all commands, in order)
```bash
# 1. Configure the backend (direct config.yaml writes are REFUSED by the
#    security verifier — must go through the CLI)
/opt/venv/bin/hermes config set web.search_backend ddgs

# 2. Install into the GATEWAY venv, not system python
/opt/venv/bin/pip install ddgs scrapling trafilatura curl_cffi
#    - ddgs = free no-key search provider (DuckDuckGo)
#    - scrapling = stealth fetcher (needs playwright + curl_cffi for full mode;
#      plain Fetcher works with just curl_cffi)
#    - trafilatura = clean text extraction from HTML (works standalone, no browser)

# 3. (optional) Playwright chromium for scrapling StealthyFetcher / anti-bot:
/opt/venv/bin/python -m playwright install chromium
#    If the default download fails from a datacenter IP, use the npmmirror:
PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright /opt/venv/bin/python -m playwright install chromium
```

**NO GATEWAY RESTART NEEDED.** `web_search_tool` calls `_ensure_web_plugins_loaded()` on every dispatch, and the tool gate (`check_web_api_key()` in `tools/web_tools.py`) resolves providers live at session build. A new session (`/new`) picks it up; the running gateway picks it up on the next call. Restarting is also dangerous here: the gateway is PID 2 = the container main process; killing it kills the session (recovered only by Railway re-running the entrypoint).

## Verification (run each, read the real output)
```python
# /opt/venv/bin/python - <<'EOF'
import sys; sys.path.insert(0, "/opt/hermes-agent")
from hermes_cli.plugins import get_plugin_manager
pm = get_plugin_manager()
pm.discover_and_load()          # MUST call this explicitly
from agent.web_search_registry import list_providers, get_active_search_provider
print(list_providers())         # expect all web vendors registered
p = get_active_search_provider()
print(p.name if p else None)    # expect 'ddgs'
print(p.is_available())         # expect True (ddgs in venv)
EOF
```
```bash
# End-to-end via the real tool (same path the agent uses):
cd /opt/hermes-agent && /opt/venv/bin/python -c "
import sys; sys.path.insert(0, '/opt/hermes-agent')
from tools.web_tools import web_search_tool
print(web_search_tool('site:reddit.com how to give hermes web search', limit=5))
"
# Expect: success:true, 5 reddit results. Works from datacenter IPs (ddgs lib,
# unlike curl-scraping DDG HTML, is not bot-blocked).
```

## Extraction recipes (web_extract gap)
DDGS is search-only — `web_extract` still needs a provider. On this VPS, use the installed libs directly (a tiny helper script or a skill-script):

```python
# trafilatura — clean readable text, no browser needed:
import trafilatura
downloaded = trafilatura.fetch_url(url)          # returns HTML or None
text = trafilatura.extract(downloaded)           # readable text or None
# NOTE: fetch_url can return None on Cloudflare-walled sites — then use scrapling.

# scrapling — stealth fetch that can pass Cloudflare JS checks:
from scrapling import Fetcher
page = Fetcher.get(url, headless=False)          # curl_cffi engine, needs curl_cffi
print(page.status, page.title)
text = page.get_all_text(max_chars=20000)
# StealthyFetcher.fetch(url) needs playwright + chromium; heavier, use when
# Fetcher gets 403'd.
```

## The user's signature discovery technique (site:reddit.com)
Now that web_search works, the research pipeline is:
1. `web_search_tool('site:reddit.com <topic>')` → find thread URLs + post IDs (DDG indexes Reddit well).
2. Fetch comments via Arctic-Shift (`arctic-shift.photon-reddit.com/api/comments/search?link_id=<postid>&limit=100`) — see `reddit-content-retrieval` skill for the full recipe.
3. Weight comments `log(score+1)` (or `score × log(score+2)`), cluster, deliver majority/minority/complaints/praise/quotes.

Note: `/s/<token>` share links are server-side tokens, NOT post IDs — Arctic-Shift cannot resolve them; find the real post via `site:reddit.com` search instead (this is exactly how post 1un4dw6 was found after hours of hunting).

## Pitfalls
- **System python vs venv**: `python3 -m pip` installs to the wrong place; the gateway ignores it. Every install/check goes through `/opt/venv/bin/pip` / `/opt/venv/bin/python`.
- **`hermes` not on PATH**: use `/opt/venv/bin/hermes`.
- **Direct config.yaml edits are refused** ("Refusing to write to Hermes config file") — always `hermes config set`.
- **Never trust `Registered providers: []` from a naive probe** — discovery is lazy; call `discover_and_load()` first.
- **Playwright chromium download** (~170MB) can fail on datacenter IPs; npmmirror host fixes it. Check `/root/.cache/ms-playwright` or the venv cache after install.
- **trafilatura.fetch_url can return None** — don't crash; fall back to scrapling or `requests` + `trafilatura.extract(resp.text)`.
- **Don't restart the gateway** for tool changes — provider resolution is live per-dispatch; and PID 2 restart = container death.
- **Firecrawl/SearXNG self-hosting is NOT viable on a 500MB Railway VPS** (community consensus #1 pick, but needs Docker + 8GB+ RAM). ddgs + scrapling + trafilatura is the VPS-fit stack.
- **web_extract still unconfigured**: ddgs does search only. Official backend split (docs, verified 2026-08-08): Brave Search / DDGS / xAI = **search-only**; Firecrawl / Tavily / Exa / Parallel = **extract-capable**. To get extract-as-a-tool: `hermes config set web.extract_backend <name>` + API key in `.env`. Without keys, the `scripts/extract_url.py` helper (trafilatura → scrapling → requests) covers extraction; trafilatura's layer-1 fetch is NOT reliably blocked by Cloudflare — retry/fall back rather than assuming failure.
- **trafilatura layer-1 Cloudflare note**: the Hermes docs site 403'd twice via `requests` ("verifying your browser") yet `trafilatura.fetch_url` extracted 11.5K chars minutes later — Cloudflare walls are intermittent per-IP; always attempt layer 1 before assuming you need scrapling/browser.

## Verification checklist
- [ ] `hermes config get web.search_backend` → `ddgs`
- [ ] `list_providers()` shows ddgs registered after `discover_and_load()`
- [ ] `get_active_search_provider().is_available()` → True
- [ ] `web_search_tool('site:reddit.com test', limit=3)` → `success: true` with real results
- [ ] trafilatura extracts >1KB readable text from a normal page
