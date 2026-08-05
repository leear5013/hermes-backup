# API model enumeration and free-tier discovery

## When to use
User shares an API key for a new provider/router and wants to know which models they can actually access (free vs paid). This is the "what am I allowed to use?" workflow.

## Step 1: Enumerate available models
```bash
curl -s "{base_url}/models" -H "Authorization: Bearer {key}"
```
Returns `{"data": [{"id": "...", "owned_by": "..."}]}`. Extract all model IDs.

## Step 2: Test each model with a minimal prompt
For each model ID, send a simple request and check for success vs access-denied:
```python
body = json.dumps({
    "model": model_id,
    "messages": [{"role": "user", "content": "OK"}],
    "max_tokens": 10,
    "temperature": 0,  # NOTE: some models require temperature=1 (e.g. kimi-k2.5)
    "stream": False     # CRITICAL: set stream=false explicitly
})
```

**Shell escaping pitfall:** Never pass JSON via `-d '...'` with single quotes in bash — shell escaping of nested quotes breaks the payload. Always write the body to a temp file and use `-d @file.json`.

## Step 3: Classify results
Parse each response:
- `"error"` with `"Access restricted"` or `"Deposit required"` → **paid tier**
- `"error"` with model-specific constraint (e.g. `"invalid temperature"`) → **accessible but needs param adjustment** — retry with corrected params
- Successful response with content → **free tier ✅**
- Empty response → likely streaming issue; add `-N` flag to curl and retry

## Gotchas hit in the field
- **Streaming responses:** some models return SSE by default even with `stream:false`. Use `curl -sN` (disable buffer) and `-w "\nHTTP:%{http_code}"` to get the full response.
- **Temperature constraints:** kimi models require `temperature:1` — passing 0 returns a helpful error, not an access denial. Distinguish "access denied" from "invalid request" in your classification.
- **Empty responses:** curl may return empty for valid responses due to buffering. The `-N` flag (or writing to file with `--max-time`) fixes this.
- **50 tool-call limit:** if testing 30+ models, you'll hit the execute_code limit. Batch models into groups of ~15 per script invocation.

## Worked example (b.ai router, 2026-08)
Provider: `api.b.ai` (multi-provider router with Azure GPT, MixAI Claude, Vertex Gemini, MiniMax, Qwen, DeepSeek).
- 38 models listed
- 3 free: `minimax-m2.7`, `kimi-k2.5` (temp=1), `qwen3.6-27b`
- 35 paid (deposit required): all GPT-5.x, all Claude, all Gemini, DeepSeek v4, minimax-m3, qwen3.8-max, glm-5.x, kimi-k2.6/k3
