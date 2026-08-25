# bore.pub tunnel → live iOS web-widget (host without public domain)

Verified 2026-08-25. Railway boxes ship with NO public URL by default:
`RAILWAY_URL` and `RAILWAY_PUBLIC_DOMAIN` are empty; only
`RAILWAY_PRIVATE_DOMAIN=*.railway.internal` exists (not reachable from a phone).
To give the phone a URL, tunnel the local ticker through bore.pub.

## Steps (exact, verified)
1. Run the ticker on a port: `python3 duty_ticker.py 8123`
   (terminal background=true — servers never exit; verify with
   `curl -sS -o /dev/null -w "%{http_code}" http://127.0.0.1:8123/` → 200)
2. Get bore (pip package `bore-cli` does NOT exist; install the Rust binary):
   - `curl -sS -m 30 -L "https://github.com/ekzhang/bore/releases/download/v0.6.0/bore-v0.6.0-x86_64-unknown-linux-musl.tar.gz" -o /tmp/bore.tgz`
   - `tar xzf /tmp/bore.tgz -C /tmp` → binary at `/tmp/bore`
   - `bore --version` → `bore-cli 0.6.0`
   - Asset name gotcha: `x86_64-unknown-linux-gnu` variant is NOT published (404);
     the `-musl` one is the right download.
3. Tunnel: `/tmp/bore local 8123 --to bore.pub` (background=true, silent)
   - Log line: `connected to server remote_port=30491` and
     `listening at bore.pub:30491` → the public URL is `http://bore.pub:30491`
   - NOTE: bore serves plain HTTP only (`https://bore.pub:<port>` fails 000;
     `http://` returns 200).
4. Verify from outside: `curl -sS -m 15 "http://bore.pub:<port>/"` → 200 + content.
5. Give the user `http://bore.pub:<port>` → Safari → Share → Add to Home Screen.

## Caveats (honest, verified)
- Free public tunnel: NOT persistent. Dies if the host restarts; port may change.
  Re-run bore and re-verify the port before handing out the URL again.
- The phone needs internet (the page itself is live-updating from the host).
- Upgrade path for permanence: bind a Railway public domain to the service,
  or run the ticker on a LAN PC (no tunnel needed, `http://<pc-ip>:8123`).

## Non-workarounds encountered (do not retry)
- `pip install bore-cli` / `pip install bore` → "No matching distribution".
- GitHub asset `bore-v0.6.0-x86_64-unknown-linux-gnu.tar.gz` → 404 (not published).
- `https://bore.pub:<port>` → 000 (bore is HTTP-only).
- Making a private GitHub repo's branch public to serve the .ics (raw URL 404
  while repo is private) → requires repo visibility change; avoid unless user
  explicitly approves exposing the vault.
