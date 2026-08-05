---
name: hermes-model-identity
description: Use when asked which model a Hermes session uses.
---

# Resolving which model a Hermes session is using

Users frequently ask "which model am I talking to?" — and the configured model id is often a **router alias** (e.g. `oc`, `gpt-5.3`) that does not reveal the underlying weights/provider. This skill is the diagnostic path to resolve it.

## Steps

1. **Session metadata first.** The session header usually names the model + provider (e.g. `Model: oc`, `Provider: openai-api`). Treat the model id as an alias until proven otherwise.
2. **Check global config** `~/.hermes/config.yaml` — frequently it does NOT pin a model (it may only hold terminal/compression/onboarding keys). An empty result is normal, not a dead end; model selection lives at session/gateway level.
3. **Find the endpoint + key:**
   - `~/.hermes/.env` → `OPENAI_API_KEY`, `OPENAI_BASE_URL` (base URL of the OpenAI-compatible endpoint, often a router/proxy).
   - `~/.hermes/auth.json` → `credential_pool.<provider>[]` entries carry `base_url` + `source` (e.g. `env:OPENAI_API_KEY`).
4. **Check the cached model list** `~/.hermes/provider_models_cache.json` → per-provider `models` array. Confirms whether the alias is genuinely served, without a network call.
5. **Query the live endpoint:** `GET {base}/models` with `Authorization: Bearer $KEY`. If the alias is in the list, it is a real served model (routers often list the default first — but first-in-list is NOT proof of default).
6. **Direct probe (optional):** `POST {base}/chat/completions` with `{"model": alias, "messages": [...]}`. Inspect the response's `model` field and ask the model to self-identify. Note: the response `model` field usually **echoes the alias**, not the real model.
7. **If identity still opaque:** say so plainly. Alias → weights mapping is only known to the router operator or the model's own self-report. Do not fabricate a mapping.

## Pitfalls

- `config.yaml` missing a model pin is normal — don't report "not configured" from that alone.
- Model lists can be huge (hundreds of aliases); filter for the exact alias rather than eyeballing.
- **Malformed router responses:** some proxies return HTTP 200 with nonstandard bodies — `json.loads` may raise `JSONDecodeError('Extra data: ...')`. Read the raw body (`errors="replace"`) before parsing; this is a router quirk, NOT a broken endpoint. See references/9router-oc-case.md.
- Don't store/hardcode the API key in scripts; read it from `~/.hermes/.env` at runtime.

## Support files

- `references/9router-oc-case.md` — worked example: alias `oc` on a Railway-hosted router (file inventory, probe code, malformed-JSON quirk).