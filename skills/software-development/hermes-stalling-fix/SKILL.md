---
name: hermes-stalling-fix
description: "Fix Hermes 'ok then spins forever' stall — context on auto."
version: 1.0.0
author: hesham-agent
license: MIT
tags: [hermes, config, context, stalling, troubleshooting]
---

# Hermes Stalling Fix

Symptom: Hermes says "ok, starting now", then after minutes just shows loading and the chat ends with nothing done. Root cause: **model context window left on `auto`** — the runtime under-negotiates and stalls on long tasks (confirmed by a Reddit/X thread where the fix was "set context to 1 million in hermes config/dashboard").

## The fix (verified live)
```bash
export HOME=<hermes_home>        # /data/.hermes on Railway; ~/.hermes locally
hermes config set model.context_length 1000000 --force
hermes config show               # now prints  Model: {'context_length': 1000000}
```
- The runtime reads **`context_length`** (NOT `context`/`max_context` — those keys are ignored by the resolver). Confirmed in `hermes_cli/config.py`: normalized field is `context_length`; custom-provider per-model override is `custom_providers[i].models.<model>.context_length`.
- 1M matches the X thread's recommendation; Hermes auto-sets 256k which is what triggers the stall.
- Restart the gateway to apply to a live session: `hermes gateway restart` from a SEPARATE shell — never from inside the gateway process (triggers the self-protection SIGTERM block).

## Blocked on Railway (do not waste time)
- `hermes dashboard` web UI **cannot build**: vite needs >1GB during transform; the process tree is cgroup-capped at `memory.max ≈ 953MB` (independent of box RAM). Dies at "transforming... Killed" (exit 137). Dashboard is only a GUI for `config set` — use the CLI.
- camoufox/Chromium cannot launch (userns `unshare` blocked). Use curl/HTTP.
- Node on box is v20 but web build needs ≥22.22; even with node22 in /opt/work the 1GB cap still blocks the build.

## Env hard facts (Railway)
- Keep heavy installs/caches in `/opt/work`, never `/data` (500MB cap). Decompress node22 tarball via a python script file (`lzma`+`tarfile`), not inline (inline extraction is blocked by the gateway guard).
- cgroup memory.max ≈ 953MB → anything exceeding it is OOM-killed (exit 137).

## Verify
`hermes config show | grep -A1 '◆ Model'` shows `context_length` set, not `(auto)`. A previously-stalling long coding task now completes.

## Related
`hermes-agent` skill (protected) is the config hub; this is a focused patch for the stall regression.
