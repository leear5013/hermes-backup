# Freebuff / Codebuff API wiring — session detail (2026-08)

Repo: `github.com/CodebuffAI/freebuff` (Apache-2.0). Freebuff = free, ad-supported build of the Codebuff CLI (same codebase, `FREEBUFF_MODE=true` build flag strips paid features). Login and session API live on **codebuff.com**; freebuff.com is the marketing/login web app.

## Verdict: hybrid provider chain
CLI → `codebuff.com/api/v1/...` (their OpenAI-compatible proxy) → **DeepSeek direct API primary**, with aggregator fallbacks:

| Tier | Lane | Upstream | Notes |
|---|---|---|---|
| 1 | DeepSeek direct | `api.deepseek.com` (first-party account) | cheapest cache reads $0.0028/M |
| 2 | `deepseek/crof` | CrofAI aggregator | "closest to primary in behaviour and price"; cache $0.0030/M |
| 3 | `deepseek/openrouter` | OpenRouter → `streamlake/fp8` → `baidu/fp8` → `gmicloud/fp8` | last resort; `allow_fallbacks:false`; max_tokens 384,000 |
| (retired) | `infron/makora` | Infron | retired 2026-08-11 — cache reads $0.0176/M (5.9x CrofAI) blew bill $9k→$39.7k/day over 4 days |

Lane ids persist in `free_session.provider_route` and are read back unvalidated — retired ids stay recognized so pinned sessions degrade instead of crash.

## Endpoint map (client-visible)
- `POST/GET/DELETE /api/v1/freebuff/session` — session admission/queue (base = `NEXT_PUBLIC_CODEBUFF_APP_URL` || `https://codebuff.com`)
- `POST /api/auth/cli/code` → `{fingerprintId}` → returns login URL + expiresAt (device-code flow)
- `GET /api/auth/cli/status?fingerprintId&fingerprintHash&expiresAt` — poll until authed; success yields user + token
- `GET /api/v1/me`, `POST /api/v1/usage`, `POST /api/v1/feedback`, `POST /api/agents/publish`, `POST /api/auth/cli/logout`
- `GET /api/healthz` — connection check
- Chat completions: `provider: 'codebuff'`, url `new URL(path.join('/api/v1', endpoint), getWebsiteUrl())`, `Authorization: Bearer <CODEBUFF_API_KEY>`

## Wire headers (free-mode session)
- `x-freebuff-instance-id`, `x-freebuff-model`, `x-freebuff-compact-session`
- `x-freebuff-acting-user-id` — **trusted server-to-server only** (selects another user's session row)
- `x-freebuff-multi-session` ('1' = Desktop concurrent tabs), `x-freebuff-heartbeat` (45s interval liveness beat)
- `x-freebuff-takeover-instance-id` — "Use it here": ends the named holder's session
- `x-freebuff-include-unused-rate-limits`
- BYOK: `x-openrouter-api-key` header (client's own OpenRouter key routed through backend)

## Login / auth detail
- Env: `CODEBUFF_API_KEY`; stored: `~/.config/manicode/credentials.json` (note: `manicode`, not `codebuff`)
- `getWebsiteUrl()`: `getRuntimeAppUrlFromEnv()` (`NEXT_PUBLIC_CODEBUFF_APP_URL` / `CODEBUFF_APP_URL`) ?? bundle-time value
- Session error surface: 403 `country_blocked|banned`, 409 `model_locked|model_unavailable`, 429 `rate_limited|spend_limited|ip_capped` + free-mode capacity deferral `429 {"error":"free_mode_capacity_deferred"}` (retry-after honored)

## Models (picklist)
- `deepseek/deepseek-v4-pro` (default; 1M ctx; reasoning low/high/max), `deepseek-v4-flash` (limited mode), MiniMax M3, MiMo 2.5, GLM 5.2 (earned), Gemini 3.1 Flash Lite (specialist only). Region gating: non-supported countries/VPN → limited tier (Flash + MiMo, 6×1h sessions/day). Premium models carry per-day session caps; free tier is ad-supported.

## Anti-abuse catalog (what they detect)
- **Cloudflare `cf-worker` header + `cf-ray` corroboration**: detects Cloudflare-Worker-based proxy/reseller services (e.g. `pingmike2/freebuff2api-wokers` pools harvested tokens and resells as OpenAI-compatible endpoint). Edge-stamped, cannot be removed by caller; modes off/observe/block/ban; allowlist for own zones. Historical false-positive: 659-account ban fully reversed (2026-08-03).
- **Byte-exact system-prompt gate**: free-mode root must open with canonical "You are Buffy..." string at position 0 (previous substring gate defeated by prompt-injection prefix `You are Buffy. [System Override: ...]`).
- **Publisher-spoof-safe agent checks**: agent id + publisher must be internal or `codebuff`, and model must be in that agent's allowed set.
- **Model lock/queueing**: per-model queues, session pinning with re-pin on each fallback hop, liveness heartbeats, takeover instance header, 30-min drain grace after `expires_at`.
- **Rate limits**: per-model + IP caps (`ip_capped`), spend limits.
- **CLI launcher force-updates** on every start (compiled-in prompts get updated).

## Source pointers (2026-08 clone)
- `sdk/src/impl/model-provider.ts` — the `provider: 'codebuff'` OpenAI-compatible client, usage accounting (`usage.cost`, `cost_details.upstream_inference_cost`)
- `common/src/constants/provider-routes.ts` — all lane constants + production postmortems
- `common/src/constants/freebuff-models.ts` — headers, model list, data-use (`FREEBUFF_TRACED_MODEL_IDS` = training-traced models)
- `common/src/constants/cf-worker-signals.ts` — worker-resale detector
- `common/src/constants/free-agents.ts` — free-mode agent/model gates, canonical prompt openings
- `cli/src/utils/freebuff-session-api.ts`, `cli/src/utils/codebuff-api.ts`, `cli/src/login/login-flow.ts` — session + login flows
- `SECURITY.md` — report to support@codebuff.com, no public GitHub issues
