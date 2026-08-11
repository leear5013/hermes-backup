# Paste-ready restore instruction (message the user hands to another Hermes)

Use when the user asks "what should I tell the other Hermes?" / "restore me on another
instance" / "he will have the same GitHub repo access". Fill the placeholders, hand the
quoted block over verbatim. This user's default backup repo: `leear5013/hermes-backup`.

> Restore my Hermes backup from **github.com/OWNER/REPO**. It's a full snapshot of my
> `~/.hermes` — SOUL.md persona, all skills, memories (USER.md + MEMORY.md), full chat
> history in `state.db`, and cron jobs.
>
> Load the `hermes-backup-restore` skill and follow it: clone the repo → secret-audit for
> live tokens → merge missing skills at `<category>/<skill>` granularity → copy memories +
> SOUL.md (timestamp-backup mine first) → recreate cron jobs via the `cronjob` tool (don't
> copy `cron/jobs.json` raw) → verify the two-level diff is clean.
>
> Auth: same GitHub access as mine — use `~/.git-credentials` with the x-access-token
> (`git config --global credential.helper store`), tokenless pushes, no PATs in scripts.
>
> ⚠️ `.env` and `auth.json` are NOT in the repo by design — ask me for API keys / Telegram
> bot token. `state.db` has secrets redacted (`***REDACTED***` markers), so history will
> have a few holes. After merging, run `hermes curator adopt` on the imported skills so
> they can be patched.

## Caveats to tell the user when handing this over
- **Same GitHub account ≠ same local token.** A different machine needs its own
  `~/.git-credentials` copy (the file is not in the repo) or the PAT handed over
  separately — the message above assumes the new box already has working auth.
- **Chat history DOES transfer** — `state.db` is in the backup (redacted), so
  `session_search` on the new instance finds the old sessions.
- **`config.yaml` stays instance-specific** — per-capability keys like `web.search_backend ddgs`
  must be re-set on the new box via `hermes config set` (direct writes are refused).
- **Verify the backup repo is current BEFORE promising**: clone/`git log --oneline -1` +
  check that `memories/`, `skills/`, `state.db` are actually present. A stale or incomplete
  repo makes the paste-ready message wrong.
- Cron jobs: only the pure-script jobs transfer cleanly (`no_agent=True`, `deliver=local`,
  `script=backup-to-github.sh`); LLM jobs need prompt re-review on the new instance.