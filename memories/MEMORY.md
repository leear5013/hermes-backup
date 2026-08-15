User: AI/LLM enthusiast (Hermes, DeepSeek, opencode). Dual-mode SOUL.md; honest 'what is knowable' answers; real user opinions over marketing. Real-time status updates during background tasks — silence unacceptable. Interested in DE/DevOps hackathons.
§
Auth via /data/.git-credentials (x-access-token; HOME=/data — authenticated GH API/code-search; MUST use 'Authorization: Bearer' — 'token' scheme 401s; search limit 30/min); state.db redacted pre-push
§
Hermes on Railway: use /opt/venv/bin/{python,hermes} (NOT system python3); gateway pkgs via /opt/venv/bin/pip. Web search LIVE (ddgs). Extract: skill hermes-web-search-stack scripts/extract_url.py (trafilatura→scrapling→requests).
§
nm-vmess:// CRACKED 2026-08-09 (NetMod 4.2.0.635): base64 → AES-128-ECB whole-payload try-loop over 3 keys until pkcs7-valid; key0 <n3t5yn4^n3tm0d> (digit-4) wins, then _netsyna_netmod_, nicetrybuddygoon. Decryptor in vpn-config-decryption skill. RasdAgent token NOT in .env (gateway bot → 409); recover via session_search BOT_TOKEN.
§
Storage: NEVER download heavy apps/files into /data (500MB cap — user correction 2026-08-10). All scratch/build/temp → /opt/work (1.8TB overlay).
§
Egypt ISP: at 0% quota ALL non-whitelisted dests blocked (gov sites only) — drives his VPN work. Railway VLESS sakura.proxy.rlwy.net:14210 works ONLY w/ SNI=speedtest.net; VPN app = Karing. 2026-08-11: do NOT save payload/quota-bypass techniques to memory/skills (user instruction).
§
RasdAgent decrypt bot (@RasdAgent_bot) deployed 2 ways: (1) live long-poll /opt/npvt-decrypt-bot/bot.py; (2) PythonAnywhere webhook (bot_webhook.py+wsgi.py; repo leear5013/rasdagent-decrypt-bot). Handles .npvt/.hc/.ehi/.dt/.ssc + vmess/vless/trojan/ss/nm-vmess/nm-vmess/ssh:// links. Token SEPARATE from Hermes gateway token (don't source from .env → 409). PA deploy = bot survives this box.
§
Freebuff = Codebuff's free ad-supported AI coding agent; API base www.codebuff.com/api/v1 (OpenAI-compatible, Bearer token, session-admission + exact 'You are Buffy' system-prompt gate). DeepSeek V4 routing: direct→CrofAI→OpenRouter cascade. Audit report: /opt/work/freebuff-security-report.md.