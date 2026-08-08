---
name: hermes-web-search
description: Debug Hermes web_search providers when registry is empty.
---

# Hermes Web Search Providers (config, plugins, debugging)

Use when `web_search`/`web_extract` tools error with "no provider", `list_providers()` returns `[]`, a provider shows unavailable, or you need to switch Hermes search backends (ddgs, searxng, firecrawl, tavily, exa, brave, parallel, xai).

## Provider selection (config)

- Keys in `/data/.hermes/config.yaml` under `web:`:
  - `web.search_backend` — per-capability override for web_search (e.g. `ddgs`)
  - `web.extract_backend` — per-capability override for web_extract
  - `web.backend` — shared fallback applying to both
- Resolution precedence: per-capability key → shared `backend` → single registered provider → legacy order (`firecrawl` → `parallel` → `tavily` → `exa` → `searxng` → `brave-free` → `ddgs`) → `None`.
- Set it with the CLI, NOT by editing config.yaml:
  ```bash
  hermes config set web.search_backend ddgs --force
  hermes config get web.search_backend
  ```
  Direct file writes to config.yaml are **blocked by a security guard** ("Refusing to write to Hermes config file") — use `hermes config set` (key/value args; `--force` silences the unknown-key notice, value still saved).

## Provider env vars (`.env`)

| Provider | Env var | Search | Extract | Free tier |
|---|---|---|---|---|
| Firecrawl (default) | `FIRECRAWL_API_KEY` (+`FIRECRAWL_API_URL` for self-host) | ✔ | ✔ | 500 credits/mo |
| SearXNG | `SEARXNG_URL` | ✔ | — | free self-hosted |
| Brave | `BRAVE_SEARCH_API_KEY` | ✔ | — | 2,000 queries/mo |
| DDGS | none (ddgs package) | ✔ | — | free |
| Tavily | `TAVILY_API_KEY` | ✔ | ✔ | 1,000 searches/mo |
| Exa | `EXA_API_KEY` | ✔ | ✔ | 1,000 searches/mo |
| Parallel | `PARALLEL_API_KEY` | ✔ | ✔ | paid |
| xAI (Grok) | `XAI_API_KEY` | ✔ | — | paid |

Search-only providers (Brave, DDGS, xAI) pair with Firecrawl/Tavily/Exa/Parallel for extract.

## Diagnosis chain (when registry looks empty)

1. **List toolsets**: `/opt/venv/bin/hermes tools list --platform telegram | grep -i web` — if the `web` toolset shows enabled but search still errors, continue.
2. **Check the registry** — MUST run with the gateway's interpreter:
   ```bash
   cd /opt/hermes-agent && /opt/venv/bin/python -c "
   from hermes_cli.plugins import get_plugin_manager
   pm = get_plugin_manager()
   pm.discover_and_load()   # <-- REQUIRED, it is NOT automatic
   from agent.web_search_registry import list_providers
   print([p.name for p in list_providers()])
   "
   ```
   `get_plugin_manager()` alone loads **0 plugins** — discovery is explicit. A registry that prints `[]` without calling `discover_and_load()` is a test artifact, not proof of a broken install.
3. **Resolve active provider**: `get_active_search_provider()` / `get_active_extract_provider()` — prints the configured backend (e.g. `ddgs`) if the config key landed.
4. **Check availability**: `provider.is_available()` — DDGS probes `import ddgs` (no network). False ⇒ the ddgs package is missing **in the interpreter the gateway uses**.

## Lightweight extract stack (no Docker, VPS-safe): Scrapling + Trafilatura

Community recommends SearXNG+Firecrawl self-hosted, but both need Docker/8GB RAM — impossible on a 500MB VPS. The lightweight equivalent that fits:

```bash
/opt/venv/bin/pip install scrapling trafilatura
```

- **Trafilatura** — works out of the box, zero config. `trafilatura.fetch_url(url)` → `trafilatura.extract(html, include_comments=False)` gives clean readable text (11.5K chars from the Hermes docs page in ~0.5s). This is a drop-in `web_extract`-style capability when no extract provider is configured.
- **Scrapling** — stealth/anti-bot fetcher (Camoufox/undetected options, good for Cloudflare). Its `Fetcher.get()` needs the optional **`curl_cffi`** engine — `ModuleNotFoundError: No module named 'curl_cffi'` on first use. Fix: `pip install curl_cffi` (or `pip install scrapling[all]`). `page.get_all_text(max_chars=...)` extracts readable text.
- Disk note: on Railway, pip installs land in `/opt/venv` on the overlay filesystem (TB-free), NOT the 500MB `/data` volume — installing Python packages does not consume the storage-limit budget (scrapling+trafilatura added ~48MB to the venv).
- Usage: these are library-level; wire them via a skill/script (e.g. a fetch-and-extract script the agent runs), or an MCP server — they do not register as Hermes web providers.

## Pitfalls

- **Hermes docs site is Cloudflare-protected**: plain `requests.get` on `https://hermes-agent.nousresearch.com/docs/...` can return 403 "We're verifying your browser" (31069-byte challenge page). `trafilatura.fetch_url` succeeded once, then a later plain requests fetch 403'd — flaky from datacenter IPs. If the site blocks, use the cached copy at `/tmp/websearch_docs.html` (from 2026-08-08) or a stealth fetch (scrapling).
- **System python3 ≠ gateway python.** The gateway runs `/opt/venv/bin/python` (confirm: `cat /proc/<gateway-pid>/cmdline`). System `python3` often lacks `yaml`, so `hermes_cli.plugins` import fails there with `ModuleNotFoundError: No module named 'yaml'` — that's a test-interpreter problem, NOT a code problem. Always test plugin loading with the venv python.
- **ddgs install target**: `pip install ddgs` must go into the venv (`/opt/venv/bin/pip install ddgs`), not system pip — `is_available()` imports it in the gateway's process.
- **Gateway restart semantics**: on Railway/Docker the gateway is PID 2 (container entrypoint, `exec hermes gateway`). `hermes gateway restart` targets a systemd service that doesn't exist there; killing PID 2 kills the whole container. To restart, re-trigger via the platform's supervisor (Railway redeploy) — and pre-flight first: prove a fresh venv process loads the providers before bouncing anything.
- **ddgs from datacenter IPs**: DDG HTML/API can serve bot challenges; Arctic-Shift remains the reliable Reddit read path (see `reddit-content-retrieval`).
- **DDGS search signature**: `search(query: str, limit: int = 5) -> Dict` — there is NO `max_results` kwarg; passing it raises TypeError.

## Community consensus (r/hermesagent, Jul 2026, upvote-weighted)

- Dominant self-hosted stack: **SearXNG (search) + Firecrawl (extract)**, both self-hosted/Docker. SearXNG needs JSON format enabled in `settings.yml` (`search: formats: [html, json]`).
- Zero-setup options: Tavily free tier ("works for me"), Exa ("built in… just add the API key"), DDGS (no key).
- Anti-bot browsing: Camoufox browser; Hound MCP for Cloudflare/CAPTCHA sites; agent-data.dev for Reddit/X/HN.
- Extract-on-a-budget (VPS-fitting picks): **Scrapling** (stealth fetch) + **Trafilatura** (clean text) — both pure-pip, no Docker; the SearXNG/Firecrawl Docker stack is the majority pick but needs 8GB+ RAM.
- Firecrawl self-host extract needs an LLM provider configured on the firecrawl-api container (e.g. `qwen2.5:14b-instruct`) or extract fails while scrape works.
- Docs page (authoritative): `https://hermes-agent.nousresearch.com/docs/user-guide/features/web-search` — note the `.md` variant 404s; fetch the HTML page.

## Support files
- `references/railway-empty-registry-worked-example.md` — full 2026-08-08 diagnosis: the false-diagnosis chain (system-python yaml gap, non-automatic discovery, PID-2 restart hazard), working probe code, and the config fix. Read it before touching a running gateway.
