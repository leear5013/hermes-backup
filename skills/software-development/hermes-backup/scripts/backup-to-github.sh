#!/usr/bin/env bash
# hermes-backup: sync EVERYTHING to GitHub (chat history, skills, SOUL, config, memories)
# Auto-redacts secrets before push so GitHub's secret scanning doesn't block it.
set -euo pipefail

HERMES_HOME="${HERMES_HOME:-/data/.hermes}"
BACKUP_DIR="/tmp/hermes-backup-repo"
REPO_URL="https://YOUR_GITHUB_PAT@github.com/USER/REPO.git"
BRANCH="main"

# --- clone or update ---
if [ -d "$BACKUP_DIR/.git" ]; then
    cd "$BACKUP_DIR"
    git fetch origin 2>/dev/null || true
    git reset --hard "origin/$BRANCH" 2>/dev/null || true
else
    rm -rf "$BACKUP_DIR"
    git clone --depth 1 "$REPO_URL" "$BACKUP_DIR" 2>/dev/null || {
        echo "ERROR: clone failed"
        exit 1
    }
    cd "$BACKUP_DIR"
fi

# --- copy everything ---
echo "Syncing files..."

# Clean old dirs to ensure deletions propagate
rm -rf skills memories sessions state cron hooks state.db* kanban.db*

# 1. SOUL.md (persona) + all backups
cp "$HERMES_HOME/SOUL.md" SOUL.md 2>/dev/null || true
for f in "$HERMES_HOME"/SOUL.md.bak.*; do
    [ -f "$f" ] && cp "$f" . 2>/dev/null || true
done

# 2. Chat history
cp "$HERMES_HOME/state.db" state.db 2>/dev/null || true
cp "$HERMES_HOME/state.db-wal" state.db-wal 2>/dev/null || true
cp "$HERMES_HOME/state.db-shm" state.db-shm 2>/dev/null || true

# 3. Session metadata
mkdir -p sessions
cp "$HERMES_HOME/sessions/"* sessions/ 2>/dev/null || true

# 4. Memories
mkdir -p memories
cp "$HERMES_HOME/memories/"* memories/ 2>/dev/null || true

# 5. Skills
cp -r "$HERMES_HOME/skills" skills

# 6. Config
cp "$HERMES_HOME/config.yaml" config.yaml 2>/dev/null || true

# 7. Cron
mkdir -p cron
cp -r "$HERMES_HOME/cron/"* cron/ 2>/dev/null || true

# 8. Kanban
cp "$HERMES_HOME/kanban.db" kanban.db 2>/dev/null || true

# 9. Platform state
cp "$HERMES_HOME/channel_directory.json" channel_directory.json 2>/dev/null || true
cp "$HERMES_HOME/gateway_state.json" gateway_state.json 2>/dev/null || true

# 10. Hooks + state dir
mkdir -p hooks state
cp -r "$HERMES_HOME/hooks/"* hooks/ 2>/dev/null || true
cp -r "$HERMES_HOME/state/"* state/ 2>/dev/null || true

# 11. .initialized
cp "$HERMES_HOME/.initialized" .initialized 2>/dev/null || true

# --- auto-redact secrets from state.db ---
python3 << 'PYEOF'
import os, json
hermes = os.environ.get("HERMES_HOME", os.path.expanduser("~/.hermes"))
secrets = set()
# From .env
env_path = os.path.join(hermes, ".env")
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            if "=" in line and not line.startswith("#"):
                val = line.split("=", 1)[1].strip().strip("\"'")
                if len(val) > 10: secrets.add(val.encode())
# From auth.json
auth_path = os.path.join(hermes, "auth.json")
if os.path.exists(auth_path):
    try:
        with open(auth_path) as f:
            data = json.load(f)
        for pool in data.get("credential_pool", {}).values():
            for cred in pool:
                for key in ("base_url", "label", "secret_fingerprint", "id"):
                    v = str(cred.get(key, ""))
                    if len(v) > 8: secrets.add(v.encode())
    except: pass
# Redact
sdb = "state.db"
if os.path.exists(sdb) and secrets:
    data = open(sdb, "rb").read()
    replaced = 0
    for secret in secrets:
        cnt = data.count(secret)
        if cnt: data = data.replace(secret, b"***REDACTED***"); replaced += cnt
    if replaced:
        open(sdb, "wb").write(data)
        print(f"Redacted {replaced} secret(s) from {sdb}")
PYEOF

# --- commit and push ---
git add -A
if git diff --cached --quiet; then
    echo "No changes — nothing to push."
    exit 0
fi
TIMESTAMP=$(date -u '+%Y-%m-%d %H:%M UTC')
FILE_COUNT=$(git diff --cached --numstat | wc -l)
git commit -m "auto-backup: $TIMESTAMP ($FILE_COUNT files)"
git push origin "$BRANCH" 2>&1 | tail -5
echo "Backup pushed: $TIMESTAMP | $FILE_COUNT files changed"
