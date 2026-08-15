---
name: ai-backend-recon
description: "Use when tracing an AI product's LLM: direct API vs proxy."
version: 1.0.0
author: curator
license: MIT
metadata:
  hermes:
    tags: [ai, llm, providers, openrouter, reverse-engineering, deepseek, inference, api]
    category: research
    related_skills: [codebase-inspection, hermes-web-search-stack]
---

# AI Backend Recon — Who Actually Powers This AI Feature?

Determining whether an AI product talks to a model vendor directly (`api.deepseek.com`, `api.openai.com`, `api.anthropic.com`) or through an inference aggregator/proxy (OpenRouter, Together, Groq, Fireworks, Novita, CrofAI…), and mapping the fallback cascade. Most answers hide in the product's own (often open-source) client repo.

## When to Use
- "What model/provider powers X's AI?" / "is it direct DeepSeek or via an aggregator?" / "reverse engineer how product X wires its LLM"
- User wants to know if a free AI service is first-party-API, proxied, or aggregator-fed

## Steps

1. **Disambiguate the product name FIRST.** Lookalike names are common (freebuf.com = Chinese security media vs freebuff.com = AI coding agent — same-sounding, unrelated products). One `web_search "<name> what is"` + domain check in results saves many wasted searches. Confirm intent before deep-diving.

2. **Find the open-source repo.** Many AI products are open source or publish an SDK. Search `github.com <product> <company>` or check the site footer/blog for the GitHub org. Clone shallow: `git clone --depth 1 <url>`. The client repo is enough — the SERVER side of most SaaS is private, but the client ships the shared constants package, which leaks the upstream routing.

3. **Grep for provider fingerprints** (case-insensitive, across `.ts/.py/.go/.js/.json/.md`, exclude tests):
   - Direct API domains: `api.deepseek.com`, `api.openai.com`, `api.anthropic.com`, `generativelanguage.googleapis.com`, `api.groq.com`, `api.together.xyz`, `api.fireworks.ai`, `api.novita.ai`
   - Aggregator markers: `openrouter`, `provider-routes`, `baseURL`, `base_url`, `chat/completions`
   - BYOK headers: `x-openrouter-api-key` etc. — bring-your-own-key support proves an aggregator path exists

4. **Read the constants files — they encode the routing architecture.** Look for:
   - `provider-routes.ts` / `*-routes` — names the lanes (`deepseek/crof`, `deepseek/openrouter`, `infron/makora`)
   - `model-config.ts` / `model-ids.ts` — model ID format is a fingerprint: `deepseek-chat` (direct naming) vs `deepseek/deepseek-v4-pro` (OpenRouter `vendor/model` naming). Both present = hybrid, both lanes exist.
   - `hosts.ts` / `constants.ts` — base URL resolution: `getWebsiteUrl()` / `NEXT_PUBLIC_*_APP_URL` = their own backend proxy

5. **Mine the code comments — production gold.** Comments in constants files routinely contain: measured $/M-token costs, cache-read pricing, incident postmortems (dates, request counts, user counts), why a lane was retired, saturation events. These are evidence — cite them in the answer.

6. **Trace the SDK first hop.** Files like `sdk/src/impl/model-provider.ts` show client → `https://their-backend.com/api/v1/...` with `Authorization: Bearer <their key>` — NOT the vendor. The backend does the upstream routing; the client never touches the vendor.

7. **Report the cascade.** Structure: client → their proxy → primary (direct vendor API) → fallback tiers (aggregator lanes with explicit upstream order). Note `allow_fallbacks:false` = sticky lanes that preserve prompt cache — cache fragmentation is the expensive failure mode for agent workloads.

## Pitfalls
- **Client repo ≠ full picture.** The open-source client only proves the first hop. Upstream routing lives in the private server — but the routing table is usually shipped to the client as a shared package/constants file. That's the trick: the constants are the evidence.
- **Don't trust the marketing.** README says "DeepSeek V4 Pro" but the code shows which LANE serves it. Code + comments > marketing copy.
- **"Cheapest" lane ≠ primary.** Fallback lanes are chosen on cache-read price (an agent turn re-sends its whole prefix every step; ~98% of input tokens are cache reads), so the primary is often NOT the cheapest per token — the fallback cascade is, by design.
- **WAF-walled live sites**: if verification requires scraping the live product and it's behind Cloudflare/Aliyun WAF (HTTP 405 + JS challenge), prefer the repo + docs over the site — the WAF is a dead end, the repo isn't.
- **Server-side only features** (queueing, capacity deferral) are named in client code via special error codes (e.g. HTTP 429 `free_mode_capacity_deferred`) — mention them as evidence of the proxy layer's responsibilities.

## Verification
The answer is PROVEN when the repo contains: (a) model ID constants, (b) provider-route constants with explicit upstream order, (c) base-URL resolution code. If only (a) exists, the architecture is underdetermined — say what's proven vs inferred.

## References
- `references/freebuff-deepseek-case.md` — worked example: Freebuff's DeepSeek wiring (client → freebuff.com/api/v1 → DeepSeek direct → CrofAI → OpenRouter), with the production cost/incident numbers mined from code comments.
