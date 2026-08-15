# Worked Example — Freebuff's DeepSeek Wiring (2026-08)

Question: "Freebuff (the free AI coding agent by Codebuff's team) advertises DeepSeek V4 — is it direct `api.deepseek.com` or via an inference provider?" Answer found entirely from the open-source repo, no live-scraping needed.

## Lookalike trap (step 1)
- `freebuf.com` = Chinese cybersecurity media (斗象科技/Tophant), has Vulbox bug bounty — NO AI chat feature.
- `freebuff.com` = free ad-supported coding agent, open source under CodebuffAI org.
- Confusion cost ~6 wasted searches; user clarification ("I mean the second one") was the fix. Always confirm which product before digging.

## Source
`git clone --depth 1 https://github.com/CodebuffAI/freebuff.git` (75MB). Monorepo: `sdk/`, `cli/`, `common/`, `agents/`, `packages/llm-providers/`, `freebuff/`.

## Evidence trail (files that mattered)
1. `README.md` → model catalog: "DeepSeek V4 Pro 08/13" default, "DeepSeek V4 Flash 07/31" limited-mode default; GLM 5.2 (earned), Gemini 3.1 Flash Lite (specialist). Marketing layer only.
2. `common/src/constants/freebuff-model-ids.ts` → `FREEBUFF_DEEPSEEK_V4_PRO_MODEL_ID = 'deepseek/deepseek-v4-pro'` — OpenRouter `vendor/model` naming.
3. `common/src/constants/model-config.ts` → BOTH namings exist: `deepseekV4ProDirect: 'deepseek-v4-pro'` AND `deepseekV4Pro: 'deepseek/deepseek-v4-pro'` → hybrid (direct + OpenRouter lanes).
4. `common/src/constants/provider-routes.ts` → THE routing table (biggest find). DeepSeek V4 Flash lane = 3 tiers:
   - Primary: **DeepSeek direct** (their own API account)
   - Tier 2: `deepseek/crof` → CrofAI aggregator ("closest to the primary in behaviour and price")
   - Tier 3: `deepseek/openrouter` → OpenRouter `streamlake/fp8` → `baidu/fp8` → `gmicloud/fp8`, `allow_fallbacks:false`, max tokens 384,000
   - `infron/makora` lane RETIRED 2026-08-11 (see production numbers below)
5. `sdk/src/impl/model-provider.ts` → first hop: client calls `OpenAICompatibleChatLanguageModel` with `url: /api/v1/{endpoint}` on `getWebsiteUrl()`, `Authorization: Bearer <codebuff key>`. Client NEVER touches DeepSeek; their backend proxies.
6. `sdk/src/constants.ts` + `common/src/constants/hosts.ts` → base URL = `https://freebuff.com` (`NEXT_PUBLIC_CODEBUFF_APP_URL` / `FREEBUFF_WEB_URL_PROD`).
7. `common/src/constants/byok.ts` → `x-openrouter-api-key` header = BYOK OpenRouter support.

## Production numbers mined from code comments (evidence, cite-able)
- DeepSeek daily bill **$9k → $39.7k over 4 days** (volume +41%) when a one-deep pinned fallback (`makora`, Infron) became the landing spot — cache-read pricing made it 5.9x on the dominant token class. Retired 2026-08-11.
- `makora` offline incident 2026-07-26/27: 1,160 requests / 191 users wedged ~32h (fixed in PR #1045).
- Infron saturation storm: 4,997 sessions diverted → 13,286 429s → aggregator ran out of credits.
- Why cache-read price dominates: agent turn re-sends whole prefix each step → ~98% of input tokens are cache reads. OpenRouter lane cache-read: `streamlake/fp8` $0.0176/M vs DeepSeek direct $0.0028/M (deliberately NOT pointed back at `deepseek` endpoint — "divert an outage onto itself").
- MiMo lane cost attribution (2026-08-01, 6h): Novita $0.138/M in + 19.2% cache vs Xiaomi direct $0.018/M + 90.5% cache.
- Free-mode capacity deferral: HTTP 429 body `free_mode_capacity_deferred` — queueing/shedding lives in their proxy.
- Context window: 1,048,576 for both DeepSeek V4 models; reasoning efforts low/high/max.

## Final answer shape
Client (CLI/Desktop/Web) → `freebuff.com/api/v1` (their OpenAI-compatible proxy: auth, usage accounting, queueing, capacity shedding) → PRIMARY DeepSeek direct API → fallbacks CrofAI → OpenRouter (sticky per-session pins). "Direct or aggregator?" → **both: hybrid with direct-first cascade.**

## Reusable technique notes
- The private server's routing table was shipped in a shared constants package — the client monorepo IS the architecture leak. Grep `provider-routes`, `model-ids`, `*-models.ts`.
- Model-ID naming (`vendor/model` vs bare) instantly distinguishes aggregator vs direct lanes.
- Comments > README for ground truth; README is marketing.
