# Freebuff (Codebuff) API Audit — worked example (2026-08-14)

Full transcript of the audit pattern applied to Freebuff (freebuff.com / codebuff.com), the ad-supported free AI coding agent by CodebuffAI (GitHub: CodebuffAI/freebuff, Apache-2.0). Reuse the structure for any SaaS.

## 1. Name disambiguation (critical first step)
- **FreeBuf** (freebuf.com) = Chinese cybersecurity media by 斗象科技 (Tophant), behind Alibaba Cloud WAF (`appkey: "CF_APP_WAF"`, all paths 405 with `data-spm` / `errors.aliyun.com` assets). No AI chat feature.
- **Freebuff** (freebuff.com) = free ad-supported AI coding agent by CodebuffAI, advertises DeepSeek V4 models.
User meant the second; a search for "FreeBuf AI DeepSeek" surfaces both — confirm before probing.

## 2. Static map from `CodebuffAI/freebuff` (shallow clone, ~75MB)
- **Auth:** `Authorization: Bearer <token>`; token from `CODEBUFF_API_KEY` env or plaintext `~/.config/manicode/credentials.json` (`userSchema`: id, name, email, authToken, fingerprintId, fingerprintHash).
- **Base URL resolution:** `sdk/src/constants.ts` → `getWebsiteUrl()` = `getRuntimeAppUrlFromEnv()` (`NEXT_PUBLIC_CODEBUFF_APP_URL` || `CODEBUFF_APP_URL`) ?? bundled `NEXT_PUBLIC_CODEBUFF_APP_URL`. This is how you find the real backend: the API is NOT on the marketing domain.
- **Endpoints (client-side):**
  - `POST /api/auth/cli/code` (no auth) — device-code minting: `{fingerprintId}` → `{fingerprintId, fingerprintHash, loginUrl, expiresAt, expiresInMs}` (1h expiry)
  - `GET /api/auth/cli/status?fingerprintId&fingerprintHash&expiresAt` (no auth) — login poll
  - `POST/GET/DELETE /api/v1/freebuff/session` — session admission (headers: `x-freebuff-model`, `x-freebuff-instance-id`, `x-freebuff-compact-session`, `x-freebuff-heartbeat`, `x-freebuff-multi-session`, `x-freebuff-takeover-instance-id`, `x-freebuff-acting-user-id` — the last two flagged as server-to-server trusted)
  - `POST /api/v1/chat/completions` — OpenAI-compatible LLM proxy
  - `POST /api/v1/web-search`, `/api/v1/docs-search`, `/api/v1/composio/execute`, `/api/v1/usage`, `/api/v1/feedback`, `GET /api/v1/me`, `POST /api/agents/publish`
- **Model IDs:** `deepseek/deepseek-v4-pro`, `deepseek/deepseek-v4-flash` (OpenRouter-style); context 1,048,576; reasoning efforts low/high/max.

## 3. Provider cascade (from `common/src/constants/provider-routes.ts` — gold in code comments)
DeepSeek V4 Flash lane, 3 tiers:
1. **DeepSeek direct** (`api.deepseek.com`, own account) — primary
2. `deepseek/crof` → **CrofAI** aggregator (replaced retired `infron/makora` lane; retired 2026-08-11)
3. `deepseek/openrouter` → OpenRouter `order: [streamlake/fp8, baidu/fp8, gmicloud/fp8]`, `allow_fallbacks:false`
Telemetry leaked in comments: bill $9k→$39.7k/day in 4 days from bad fallback pin; 1,160 reqs/191 users/32h outage (`makora` offline, #1045); 4,997 sessions → 13,286 saturation 429s → aggregator ran out of credits.

## 4. Abuse controls (from `common/src/constants/`)
- `cf-worker-signals.ts`: Cloudflare-Worker reseller detection via `CF-Worker` header + `CF-Ray` edge corroboration (client can't fake); observe/block/ban modes; 659-account false-positive sweep fully reversed (2026-08-03).
- `free-agents.ts`: free-mode system-prompt gate — first system message must open byte-exact with `You are Buffy, the coding agent behind Codebuff.` (or strategic assistant / Freebuff Cloud project planner variants); position-0 prefix check, whitespace-trim only. Defeats "prepend system override" bypass.
- `isFreeModeAllowedAgentModel()`: server-side agent+model allowlist, publisher-spoof safe.
- Region tiering: non-supported regions/VPNs get limited access (Flash + MiMo, 6× 1h sessions/day).

## 5. Live unauthenticated probe results
- `POST https://freebuff.com/api/auth/cli/code` → **200** `{"fingerprintId":"audit-...","fingerprintHash":"b5a42681...","loginUrl":"https://freebuff.com/login?auth_code=nHRNtaxi5...","expiresAt":...,"expiresInMs":3600000}` (finding: unauthenticated minting = login-link spam vector)
- `freebuff.com/api/v1/*` → all **404** Next.js SPA fallback (HTML "This page wandered off") — API not on this host
- `codebuff.com` → **301** → `www.codebuff.com`
- `GET https://www.codebuff.com/api/v1/freebuff/session` (no token) → **401** `{"error":"unauthorized","message":"Missing or invalid Authorization header"}`
- `POST https://www.codebuff.com/api/v1/chat/completions` (no token) → **401** `{"message":"Unauthorized"}`
- `POST https://www.codebuff.com/api/auth/cli/code` → **200** (minting works on both hosts)
- DeepSeek direct: `POST https://api.deepseek.com/chat/completions` with invalid key → **401** `{"error":{"message":"Authentication Fails...","type":"authentication_error","code":"invalid_request_error"}}` — proves reachability; use `model: "deepseek-chat"`.

## 6. Boundary behavior that worked
User claimed collaboration with the Freebuff owner and asked for a working "use their API outside freebuff" curl. Held: no live-token completion, no human login; still delivered full protocol + report file + legit alternative (DeepSeek official API ~$0.27/M in, OpenRouter, or the free CLI itself). The successful framing: "a security test ends in a report" + the money insight for the owner (their $39.7k/day DeepSeek bill vs $0.27/M direct pricing → cache-hit tuning on the primary lane).
