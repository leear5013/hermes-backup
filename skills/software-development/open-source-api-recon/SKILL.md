---
name: open-source-api-recon
description: "Map an AI product's API wiring: provider, auth, endpoints"
version: 1.0.0
author: hermes-curator
license: MIT
metadata:
  hermes:
    tags: [reverse-engineering, api, provider-routing, auth, security-audit, open-source, llm]
    category: software-development
---

# Open-Source API Recon

Reverse-engineer how a product's AI backend is wired — which LLM provider serves it (direct vs aggregator/proxy), the auth flow, the endpoint surface, and the anti-abuse controls — from its open-source client code. Use for: understanding a product's architecture, assessing whether its API could be called externally, or friendly security audits (abuse-resistance review of a platform).

## When to use
- User asks "how does X's AI work — direct DeepSeek or through an inference provider?"
- User wants to call a product's API outside its official clients ("reverse engineer it")
- Friendly security audit of an open-source AI platform ("is it protected well?")
- Understanding a product's architecture from published code

## Workflow
1. **Identify the artifact.** Check for an open-source repo (product site usually links the GitHub org). Open source beats black-box probing — no WAF fights.
2. **Shallow clone** (`git clone --depth 1`) and orient: `package.json` workspaces, README model mentions, `SECURITY.md` (disclosure channel — cite it in any audit writeup).
3. **Find provider wiring — grep the constants, not the business logic:**
   ```bash
   grep -rnE 'api\.deepseek\.com|openrouter|api\.anthropic\.com|api\.openai\.com|generativelanguage' --include='*.ts' common src packages | grep -v __tests__
   ```
   - A `provider-routes.ts` / `model-config.ts`-style file encodes the full fallback cascade: primary → aggregator lanes → OpenRouter upstream order, max-tokens caps, `allow_fallbacks` policy.
   - Model ID format tells the lane: `vendor/model` = OpenRouter-style; bare `model-name` = provider-native.
4. **Read the code comments — the goldmine.** Production incident postmortems (outage request counts, $/day bills, 429 storms), live-measured per-lane pricing, why lanes were retired. They read like honest ops docs and are the most valuable output of the whole exercise.
5. **Trace client → server base URL:** SDK `client.ts` / `model-provider.ts` → `getWebsiteUrl()`/`getBaseUrl()` → env override (`NEXT_PUBLIC_*_APP_URL`) else bundle-time default. Clients usually talk to the product's OWN proxy (`/api/v1/...`), not the LLM vendor directly — that's the "direct vs proxied" verdict for the user's surface.
6. **Map the auth flow:** device-code login endpoints (`/api/auth/cli/code` → poll `/status`), token env var, credentials file (`~/.config/<vendor>/credentials.json`). The API key the CLI uses IS the product's session token.
7. **Catalog anti-abuse controls** — the codebase documents its own defenses: edge/WAF headers, fingerprint gates (byte-exact system-prompt checks), rate limits + capacity deferrals, country/IP gating, session pinning + heartbeats, BYOK passthrough. See `references/freebuff-codebuff-wiring.md` for a full catalog.
8. **Deliver:** architecture chain (client → proxy → provider cascade), the direct/hybrid/proxied verdict, honest external-use assessment (token required, ToS, detection risk), and for security audits: disclosure channel + concrete findings.

## Pitfalls
- **The repo is the client, not the server.** Server-side gating (free-mode admission, billing) is often private. Client code reveals endpoints + headers, not full server logic — say what is client-derived vs inferred.
- **Secrets scans hit eval fixtures.** `evals/` JSON benchmarks embed fake diffs containing key-shaped strings — exclude `evals/` from secret scans.
- **WAF 405s don't matter when the repo is public.** The site may 405 everything from curl (Alibaba Cloud WAF + JS challenge) while the source is fully readable — switch to the repo.
- **Lookalike names are different products** (FreeBuf vs Freebuff). Verify which one the user means before deep-diving.
- **The answer is usually "hybrid"**: direct-first with aggregator fallbacks (e.g. CrofAI → OpenRouter). Check provider-route constants before concluding "direct".
- **"Can I use their API?" framing:** token-gated + ToS + detectable. Offer the legit path (vendor's own API, BYOK headers) alongside the honest risk picture. For friendly audits, frame findings as what the vendor should fix, not a how-to-exploit.

## Support files
- `references/freebuff-codebuff-wiring.md` — full Freebuff/Codebuff session detail: endpoint map, wire headers, DeepSeek provider cascade with pricing, anti-abuse catalog, login flow.
