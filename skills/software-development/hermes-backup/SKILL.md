---
name: hermes-backup
description: Use when backing up or restoring Hermes state to a git repo.
---

# Backing up Hermes Agent to a GitHub repo

Back up the full Hermes state — persona, skills, memories, chat history, config, cron jobs — to a GitHub repo so a new bot can restore it in one shot.

## What gets backed up

| File/directory | Contents |
|---|---|
| `SOUL.md` + `SOUL.md.bak.*` | Persona + all backups |
| `skills/` | All installed skills (procedural memory) |
| `memories/` | MEMORY.md, USER.md (user profile, personal notes) |
| `state.db` | Full chat history across all sessions (SQLite) |
| `sessions/sessions.json` | Session metadata |
| `config.yaml` | Terminal, compression, onboarding settings |
| `cron/` | Cron job definitions + execution history |
| `kanban.db` | Task board (if used) |
| `channel_directory.json` | Platform mappings |
| `gateway_state.json` | Gateway runtime state |
| `hooks/` | Hook scripts |
| `state/` | Gateway heartbeat, etc. |

## What is EXCLUDED (security)
- `.env` — API keys, tokens (OPENAI_API_KEY, TELEGRAM_BOT_TOKEN, etc.)
- `auth.json` — credential pool, base URLs, fingerprints
- Image/audio/cache directories

## The critical pitfall: GitHub secret scanning

When backing up `state.db` (chat history), **GitHub's push protection detects embedded secrets** — API keys, tokens, or PATs that appear in conversation transcripts. The push will be rejected with `GH013: Repository rule violations found`.

**Two-layer redaction is required:**

**Layer 1 — Known secrets from config files:** Read `.env` and `auth.json` to build a set of known secret values (API keys, base URLs, fingerprints). Replace each in `state.db`.

**Layer 2 — Pattern scanning for user-pasted tokens:** Users often paste GitHub PATs, API keys, or other tokens directly into chat. These are NOT in `.env` or `auth.json` — they only exist in the chat history. Scan `state.db` for common token patterns and redact them:

```python
import re, json, os
secrets = set()
# Layer 1: from .env and auth.json (same as before)
# ...
# Layer 2: scan state.db for token PATTERNS
db = open("state.db","rb").read()
gh_tokens = re.findall(rb'gh[pso]_[A-Za-z0-9]{20,}', db)  # GitHub PATs
sk_tokens = re.findall(rb'sk-[A-Za-z0-9]{20,}', db)        # OpenAI-style keys
for t in gh_tokens + sk_tokens:
    secrets.add(t)
# Apply all redactions
for s in secrets:
    db = db.replace(s, b"***REDACTED***")
open("state.db","wb").write(db)
```

**Without Layer 2, the push WILL fail** — we hit this 3 times before discovering that the chat history contained 14 GitHub PATs and 16 sk-* tokens that weren't in any config file. The error is `GH013` with locations pointing to byte offsets in `state.db`.

## Backup script pattern
See `scripts/backup-to-github.sh` for the full working script. Key structure:
1. Clone or update the repo (shallow clone)
2. Copy all files from `~/.hermes/` into the repo
3. Auto-redact secrets from `state.db`
4. `git add -A` → `git diff --cached --quiet` (skip if no changes) → commit + push

## Cron setup
Use `cronjob action=create` with `script=backup-to-github.sh`, `schedule=every 12h`, `deliver=local` (silent, no chat spam), `no_agent=True` (just runs the script, no LLM needed).

## Restore on a new bot
```bash
git clone https://github.com/<user>/<repo>.git
cp -r <repo>/* ~/.hermes/
# Only manual step: create ~/.hermes/.env with your credentials
```
The new bot gets: same SOUL.md, same skills, same memories, same chat history. Only `.env` needs manual setup (private keys can't be in the repo).

## Pitfalls
- **GitHub token in chat history:** If the user pastes a PAT into chat during a session, it gets stored in state.db. Layer 1 redaction (from .env/auth.json) does NOT catch these — you MUST also scan for token patterns (ghp_*, sk-*) directly in state.db (Layer 2). Without this, expect `GH013` push rejections with byte-offset locations pointing into state.db.
- **state.db grows over time:** The SQLite file includes all session messages. For very long-lived bots, consider periodic `VACUUM` or archiving old sessions.
- **git identity required:** Set `git config --global user.email` and `user.name` before first push, or commits will fail with "Author identity unknown."
- **The backup script embeds the PAT in the repo URL.** This is in the script file itself (not in the backed-up data). The PAT in the script should be rotated if compromised. The script auto-redacts secrets from state.db but not from its own URL — that's intentional for automation, but be aware.
