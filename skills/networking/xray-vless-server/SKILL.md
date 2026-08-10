---
name: xray-vless-server
description: Host your own VLESS server on Railway with fake-SNI evasion.
---

# Xray VLESS Server on Railway/PaaS (vpnjantit-style)

## When to use
- User wants to run their own Xray VLESS/WS server on Railway (or any PaaS / own VPS) and generate importable links for v2rayNG/NekoBox/etc.
- User asks for "fake SNI" configs (disguise traffic as a site like `mab.etisalat.com.eg`) — explain the concept exactly as below.
- User's existing repo pattern: `leear5013/xray-railway-vpn` (alpine Dockerfile + xray-config.json, VLESS/WS, port 8080).

## What "fake SNI" actually is (explain to user like this)
- SNI is a plaintext label in the TLS ClientHello, read by the firewall BEFORE encryption starts.
- Firewall sees `mab.etisalat.com.eg` → allows; ALL real traffic still goes to YOUR server. The spoofed domain is never contacted — it's a disguise word, not a hop. This is the answer to "does it pass through mab?" — no, it never does.
- The certificate belongs to YOUR server, so the client sees a name mismatch → that's why links carry `insecure=1` / `allowInsecure=1` (skip cert validation).
- Verified live 2026-08-10: `gr1.vpnjantit.com:10002` presents CN=gr1.vpnjantit.com for BOTH real and fake SNI (openssl s_client -brief), TLSv1.3 both ways.

## Two TLS-termination models (pick the right one)
1. **PaaS HTTPS edge** (Railway `.up.railway.app:443`, custom domain): edge terminates TLS with ITS cert and routes on SNI/Host. Fake SNI is REJECTED at the edge before your app sees it; `insecure` cannot help. Link MUST use `sni=<your-app>.up.railway.app`. (This is the user's existing repo.)
2. **Raw TCP passthrough** (Railway **TCP Proxy** → `*.proxy.rlwy.net:<random-port>`, or your own VPS): L4 passthrough with no edge TLS → you run TLS inside Xray with a **self-signed cert** + client `allowInsecure` → exact vpnjantit pattern, fake SNI works.

## Railway TCP Proxy recipe (model 2)
1. Dockerfile: alpine + wget/unzip Xray-linux-64.zip → `/usr/local/bin/xray`; COPY `server.crt server.key xray-config.json` → `/etc/xray/`.
2. xray-config.json: inbound port 8080, protocol vless, `streamSettings`: `network=ws`, `security=tls`, `tlsSettings.certificates=[{certificateFile:"/etc/xray/server.crt", keyFile:"/etc/xray/server.key"}]`, `wsSettings.path`.
3. Self-signed cert (CN/SAN cosmetic — server ignores requested SNI and serves this cert):
   `openssl req -x509 -nodes -newkey rsa:2048 -keyout server.key -out server.crt -days 3650 -subj "/CN=mab.etisalat.com.eg" -addext "subjectAltName=DNS:mab.etisalat.com.eg"`
4. Deploy → Railway → Settings → Networking → **TCP Proxy** → internal port 8080 → Railway assigns `shuttle.proxy.rlwy.net:PORT`.
5. Link:
   `vless://UUID@<proxy-domain>:<PORT>?encryption=none&security=tls&sni=mab.etisalat.com.eg&allowInsecure=1&type=ws&host=mab.etisalat.com.eg&path=%2F<path>#name`
6. **Caveat to tell the user up front**: TCP proxy public port is a random high port — networks/eAPNs that only allow 443 egress will block it. Trade-off, not a bug.

## Xray 26 client pitfall (discovered 2026-08-10)
- Xray-core ≥ 26.x REMOVED `allowInsecure` from `tlsSettings`: config fails to start with `The feature "allowInsecure" has been removed and migrated to "pinnedPeerCertSha256"`.
- Mobile apps (v2rayNG / NekoBox / V2Box) still accept `allowInsecure=1` in links — fine for the real deployment.
- For Xray-CLI local testing on new versions: set `pinnedPeerCertSha256` to your self-signed cert's SHA-256, or pin an older Xray release.
- Do NOT hand-roll VLESS frames in Python for E2E tests — server logs `invalid request version` and it wastes a loop. Use the real xray client binary + curl.

## Local E2E verification (do this BEFORE deploying)
1. **Download to /opt/work, NEVER /data** (user preference, 2026-08-10: /data is a 500MB cap that a 21MB xray.zip already dented):
   `curl -sL -o /opt/work/xray.zip https://github.com/XTLS/Xray-core/releases/latest/download/Xray-linux-64.zip`
2. Generate self-signed cert + write templates/xray-config.json; run `xray run -c` as a background process.
3. `echo | openssl s_client -connect 127.0.0.1:8080 -servername mab.etisalat.com.eg -brief` → expect TLSv1.3, subject CN=mab.etisalat.com.eg.
4. Real client: templates/client-config.json (socks on 10808) → `curl -s -x socks5h://127.0.0.1:10808 https://example.com -w "%{http_code}"` → expect 200.
5. After Railway deploy, same openssl probe against `<proxy-domain>:<PORT>`: YOUR self-signed cert showing = passthrough confirmed.

## Permanent cert strategy (zero-friction for user — VERIFIED)
- Generate cert ONCE locally, commit `certs/server.crt` + `certs/server.key` to the repo and `COPY` them in the Dockerfile. Build-time `openssl req` re-generates on EVERY rebuild → fingerprint changes → every saved `fp=` link dies on redeploy → user calls it "tiring". (2026-08-10: user's deployment redeployed between sessions this same way.)
- Precompute fingerprint from committed cert (`openssl x509 -in certs/server.crt -noout -fingerprint -sha256`, strip colons), bake it into README link as `&fp=<hex>`, so user never runs a command. Leave ONE placeholder (`SERVER:PORT`) in the link.
- User's only remaining manual step = the dashboard TCP-Proxy click. Give a 30-second numbered checklist + ready link.

## Verify whether the user's deployment is proxied (no dashboard access)
- App domain `xxx-production-XXXX.up.railway.app` = HTTPS edge only. TCP proxy is a SEPARATE `*.proxy.rlwy.net:PORT` domain; ports 80/443 only open + `openssl` showing `CN=*.up.railway.app` = proxy NOT enabled → tell user to click TCP Proxy (dashboard action only; no API/CLI path found).
- Quick port probe: python connect loop, timeout 1.5–2.5s/port, short candidate list, wrap in `timeout 40` (a slow 120-port scan timed out at 120s).

## Files
- templates/Dockerfile — alpine + xray + certs
- templates/xray-config.json — server config (self-signed TLS, VLESS/WS)
- templates/client-config.json — test client (socks + VLESS/WS/TLS)
- references/railway-networking.md — Railway edge/TCP-proxy doc facts + vpnjantit probe transcript

## Pitfalls
- Storage: heavy binaries on /data break the 500MB cap → always /opt/work (1.8TB overlay).
- wsSettings `path` must match between server config, client config and link `path=` — mismatch = silent 404 on WS upgrade.
- Xray config parse failure `open /etc/xray/server.crt: no such file` = cert paths must match where the Dockerfile copies them.
- WS inbound deprecation warning in logs (`WebSocket transport ... deprecated, migrate to XHTTP`) is a warning, NOT an error — VLESS+WS still runs fine (vpnjantit does exactly this).