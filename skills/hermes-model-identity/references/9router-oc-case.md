# Worked case: alias `oc` on a Railway-hosted router (2026-08-04)

## Symptom
User asked "which model am I talking with now". Session metadata showed `Model: oc`, `Provider: openai-api`. The model id looked like an opaque alias.

## Files that resolved the chain
- `~/.hermes/config.yaml` — no model pin at all; only `terminal`, `compression`, `onboarding` keys. (Absence of a pin is normal.)
- `~/.hermes/.env` — `HERMES_HOME=/data/.hermes`, `OPENAI_API_KEY=***`, `OPENAI_BASE_URL=https://9router-production-dd6c.up.railway.app/v1`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_ALLOWED_USERS`.
- `~/.hermes/auth.json` — `credential_pool["openai-api"][0]` = `{label: OPENAI_API_KEY, auth_type: api_key, source: env:OPENAI_API_KEY, base_url: https://9router-production-dd6c.up.railway.app/v1}`.
- `~/.hermes/provider_models_cache.json` — `openai-api.models` array; `oc` is the FIRST entry (matches the live listing).

## Live endpoint results
- `GET {base}/models` → 200, 590 model aliases, `oc` present (first item). Served aliases include `anthropic/*`, `ag/*`, `blackbox/*`, `cl/*`, `claude`/`gpt`/`gemini` variants, plus vendor-scoped namespaces — a typical router aggregation.
- `POST {base}/chat/completions` with model `oc` → **HTTP 200 with a body that `json.loads` cannot parse**: `JSONDecodeError('Extra data: line 1 column 1361 (char 1360)')`. Likely a nonstandard/streaming-adjacent body from the proxy. Lesson: on router proxies, read `r.read().decode(errors="replace")` raw before assuming the endpoint is broken.

## Probe snippet (reusable)
```python
import os, json, urllib.request
key = next(l.split('=',1)[1].strip() for l in open('/data/.hermes/.env')
           if l.startswith('OPENAI_API_KEY='))
base = "https://9router-production-dd6c.up.railway.app/v1"
# GET /models
req = urllib.request.Request(base+"/models", headers={"Authorization": f"Bearer {key}"})
print(json.load(urllib.request.urlopen(req, timeout=30)))
# chat probe — read raw first, parse defensively
body = json.dumps({"model":"oc","messages":[{"role":"user","content":"What model are you?"}]}).encode()
req = urllib.request.Request(base+"/chat/completions", data=body,
      headers={"Authorization": f"Bearer {key}", "Content-Type":"application/json"})
raw = urllib.request.urlopen(req, timeout=60).read().decode(errors="replace")
print(raw[:2000])  # json.loads(raw) may fail on router quirks
```

## Outcome
`oc` is genuinely served by the router, but its underlying weights/provider are unknown from the alias alone; the endpoint's `model` field echoes the alias. Reported the boundary honestly instead of inventing a mapping.
