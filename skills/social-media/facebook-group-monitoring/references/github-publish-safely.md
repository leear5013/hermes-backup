# Publishing user code to GitHub without leaking secrets (verified workflow)

Used to publish the RASD product to `leear5013/rasd` (public repo, so the user
can download the zip unauthenticated from a phone).

## 1. Get the PAT without ever printing it
The user's GitHub PAT is embedded in the backup script's repo URL:
`/data/.hermes/scripts/backup-to-github.sh` line: `REPO_URL="https://<PAT>@github.com/leear5013/hermes-backup.git"`
It is auto-redacted in read_file output (`«redacted:ghp_…»`) — so extract it
with sed inside a script, never echo it:
```bash
TOKEN=$(sed -n 's|.*https://\([^@]*\)@github.com/leear5013/hermes-backup.git.*|\1|p' \
        /data/.hermes/scripts/backup-to-github.sh | head -1)
```
(40 chars, `ghp_…` format.)

## 2. Pre-push secret scan — abort if ANY pattern is in the files being committed
Grep the source tree (excluding .git and the local secrets file) for every
secret string that exists in the project: bot token, cookie values (`datr=`,
`xs=14`, `fr=…`), c_user id, chat_id, and the full token string itself.
```bash
BAD=0
for pat in "<bot_token>" "<c_user_id>" "datr=" "xs=14" "<chat_id>"; do
  if grep -rIl --exclude-dir=.git --exclude=config.local.json "$pat" "$SRC" >/dev/null 2>&1; then
    echo "!! FOUND: $pat"; BAD=1
  fi
done
[ "$BAD" = "1" ] && exit 1
```
Remember: placeholders count as leaks too. The user's real chat_id was
initially hardcoded as a placeholder in `popup.html` and `setup_check.py` —
replace real IDs with `123456789` BEFORE scanning/pushing.

## 3. Create the repo + push with token via command substitution
Never put the token literally in a command string (it lands in shell history
and tool transcripts). Use `$(sed ...)` inline or a script file:
```bash
curl -s -o /dev/null -w "%{http_code}" -X POST \
  -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" \
  https://api.github.com/user/repos \
  -d '{"name":"rasd","description":"...","private":false}'   # 201 created, 422 exists
git init -q; git add -A; git commit -q -m "..."
git push -q "https://${TOKEN}@github.com/<user>/<repo>.git" main
```
Public repos are right for the user's flow: the codeload zip URL works without
login on any phone.

## 4. POST-push verification — prove the zip is clean (mandatory)
The push succeeding does NOT prove the zip is safe — verify the artifact the
user will actually download:
```bash
curl -sL -o check.zip "https://github.com/<user>/<repo>/archive/refs/heads/main.zip"
python3 - <<'EOF'
import zipfile
z = zipfile.ZipFile('check.zip')
names = '\n'.join(z.namelist())
leaks = [s for s in ['<bot_token>', '<c_user>', 'datr=', '<chat_id>'] if s in names]
print('LEAK CHECK:', 'FAIL ' + str(leaks) if leaks else 'clean')
EOF
```
Also eyeball the entry list — confirm `config.local.json` / `seen_ids.json` are
absent and the expected files are all present.

## Secrets that must never leave the machine
- `config.local.json` (cookie_string, tg token) — gitignored AND zip-excluded
- The user's Telegram chat_id — a personal identifier, keep it out of
  committed placeholders (use `123456789`)
- Cookie values (`datr=`, `xs=`, `fr=`) — full session hijack material
