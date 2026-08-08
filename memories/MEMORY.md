User: AI/LLM enthusiast (Hermes, DeepSeek, opencode). Dual-mode SOUL.md; honest 'what is knowable' answers; real user opinions over marketing. Real-time status updates during background tasks — silence unacceptable. Interested in DE/DevOps hackathons.
§
Reddit fetching: Arctic-Shift ids/search-subreddit/comments-tree ✅ (q= broken; comments in item["data"]); before/after take DATES → 7-day chunks. /s/ links DON'T resolve → web_search 'site:reddit.com <topic>' (ddgs works from VPS). Jina r.jina.ai blocked. Rank score×log(score+2). Never summarize single thread. Skill reddit-content-retrieval.
§
RASD v1 (Arabic FB lead watcher) at /data/workspace/rasd/.
§
9router proxy = omni-route-production-9fa0.up.railway.app/v1 (openai-api, model 'hermes', alias oc/*). OmniRoute: cookie-auth providers, huggingchat needs full Cookie header; HF free tier monthly credits. Probe /v1/models first.
§
Micro-SaaS side income research (boring industries). Likes creative skills.
§
Hermes auto-backup: repo leear5013/hermes-backup, 12h cron 'hermes-backup-github' (no_agent, deliver=local, exec wrapper). Tokenless via ~/.git-credentials; state.db redacted pre-push (ghp_*/sk-*/telegram-token patterns incl \d{8,10}:[A-Za-z0-9_-]{30,}). Restore: hermes-backup-restore skill.
§
CRITICAL: When background tasks (delegate_task, long scripts) run, give real-time progress updates every few minutes. Going silent frustrates Hesham — reported Aug 2026.
§
Hermes on Railway: gateway/CLI run /opt/venv/bin/python (NOT system python3) — install gateway pkgs via /opt/venv/bin/pip. CLI: /opt/venv/bin/hermes. Web search LIVE (ddgs). Web extract: skill hermes-web-search-stack scripts/extract_url.py (trafilatura→scrapling→requests).
§
VPN-config decrypt bot @RasdAgent_bot (token 8647570977:...) at /opt/npvt-decrypt-bot (stdlib bot.py + 5 decryptors zhgddm/npv-, deps pycryptodome/argon2/msgpack in /opt/venv; vmess/vless/trojan/ss/nm-vmess share-link decoder added). USER PREF: clean JSON only (watermark stripped), NO redaction. Skill vpn-config-decryption (template decrypt_bot.py). Bot dies on container restart — needs startup hook if permanent. web_search_tool returns JSON string → json.loads first.