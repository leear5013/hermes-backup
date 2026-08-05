# GitHub Backup with Secret Redaction

## Problem
When backing up Hermes state (including `state.db` chat history) to a public/private GitHub repo, GitHub's push protection (secret scanning) blocks commits containing API keys, tokens, or credentials embedded in the chat history.

## Solution
Auto-redact all secrets from `state.db` before committing. The redaction script scans for:

1. **Values from `.env`** — all substantial values (>10 chars)
2. **Values from `auth.json`** — base_url, label, secret_fingerprint, id fields
3. **GitHub PAT patterns** — `ghp_*`, `gho_*`, `ghs_*`, `ghr_*` anywhere in state.db (users paste tokens in chat)
4. **OpenAI-style API keys** — `sk-*` patterns anywhere in state.db

## Redaction script pattern
```python
import re, os, json

redactions = set()

# From .env
with open(os.path.expanduser("~/.hermes/.env")) as f:
    for line in f:
        if "=" in line and not line.startswith("#"):
            val = line.split("=", 1)[1].strip().strip("\"'")
            if len(val) > 10:
                redactions.add(val.encode())

# From auth.json
with open(os.path.expanduser("~/.hermes/auth.json")) as f:
    data = json.load(f)
for pool in data.get("credential_pool", {}).values():
    for cred in pool:
        for key in ("base_url", "label", "secret_fingerprint", "id"):
            v = cred.get(key, "")
            if v and len(str(v)) > 8:
                redactions.add(str(v).encode())

# Scan state.db for patterns users may have pasted
with open("state.db", "rb") as f:
    sdata = f.read()
redactions.update(re.findall(rb'gh[pso]_[A-Za-z0-9]{20,}', sdata))
redactions.update(re.findall(rb'sk-[A-Za-z0-9]{20,}', sdata))

# Apply
for secret in redactions:
    sdata = sdata.replace(secret, b"***REDACTED***")
with open("state.db", "wb") as f:
    f.write(sdata)
```

## Key lesson
GitHub's secret scanning is aggressive — it finds tokens even inside SQLite binary files. The `ghp_*` pattern in chat history is the most common blocker because users paste GitHub tokens in conversation. Always scan for pattern matches in state.db, not just .env values.

## Cron integration
Run the backup script via `cronjob` with `no_agent=True` and `script=backup-to-github.sh`. The script handles clone, copy, redact, commit, push. Use `deliver=local` to avoid chat spam.
