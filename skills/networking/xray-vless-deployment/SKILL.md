---
name: xray-vless-deployment
description: Deploy self-hosted Xray VLESS servers with fake-SNI URIs.
---

# Xray VLESS server deployment (fake-SNI style, Railway/Docker)

Use when: the user wants to deploy their OWN Xray/VLESS server (Railway, VPS, Docker), generate client URIs in vpnjantit-style anti-censorship format (`sni=mab.etisalat.com.eg&allowInsecure=1`), or debug why a self-hosted TLS/WS server won't connect.

## Architecture: why fake-SNI links need raw TCP to the server

A vpnjantit-style link:
```
vless://UUID@host:port?encryption=none&security=tls&sni=mab.etisalat.com.eg&insecure=1&allowInsecure=1&type=ws&host=mab.etisalat.com.eg&path=%2Fxyz#name
```
- The SNI is only a text label in the TLS ClientHello that the firewall reads BEFORE encryption. Traffic never passes through mab.etisalat.com.eg — it's a disguise word, not a hop.
- Requires the SERVER to terminate TLS itself (raw TCP), so it can present whatever cert it wants while the client was told "I'm talking to mab.etisalat".
- Client must skip cert validation (`allowInsecure=1`) because the served cert won't match the fake SNI.

### Verify a host supports fake SNI — probe BEFORE building
```bash
echo | openssl s_client -connect HOST:PORT -servername HOST -brief        # real SNI
echo | openssl s_client -connect HOST:PORT -servername fake.example.com -brief  # fake SNI
```
Both succeed and present the server's own cert → server terminates TLS → fake SNI works (verified: gr1.vpnjantit.com:10002 = 51.195.91.135, cert CN=gr1.vpnjantit.com, TLS1.3 both ways).
Fake SNI rejected/fails → SNI-routed edge (e.g. Railway HTTPS) → you need a TCP proxy (below).

## Railway: HTTPS edge vs TCP Proxy
- Default HTTPS (`your-app.up.railway.app:443`) terminates TLS at the edge and routes on SNI/Host → fake SNI cannot reach your app. `insecure=1` can't help; the mismatch happens at Railway's edge, not your client.
- **TCP Proxy** (Service → Settings → Networking → TCP Proxy → internal port): raw L4 passthrough, edge does NOT touch TLS → Railway assigns `*.proxy.rlwy.net:<random-port>`. This is the vpnjantit-style path. Internal port can be 443 or 8080.
- Custom domain: CNAME to the proxy host WITHOUT the port; you MUST keep Railway's assigned port. Cloudflare must be DNS-only (grey cloud).
- Caveat from docs: "If your client validates or looks for a specific hostname, it may fail" → client MUST use allowInsecure (phones) or pinnedPeerCertSha256 (Xray-core 26).
- Railway docs are Mintlify — fetchable as raw markdown by appending `.md`: `https://docs.railway.com/networking/tcp-proxy.md` (works when the HTML is JS-rendered / 404s).

## CRITICAL PITFALL: Xray-core ≥ v26 removed `allowInsecure`
Xray 26.x client config fails hard:
```
Failed to build TLS config. > The feature "allowInsecure" has been removed and migrated to "pinnedPeerCertSha256".
```
- Server side is unaffected (`tlsSettings.certificates` with self-signed files is fine).
- Xray-core client (`xray run -c client.json`): use `tlsSettings.pinnedPeerCertSha256: "<sha256-hex-of-server-cert>"`. Placeholder `"ignore"` is NOT accepted (`encoding/hex: invalid byte`).
- Phone apps (v2rayNG, NekoBox, Streisand…) bundle their own cores and still accept `allowInsecure=1` in URIs — vpnjantit-style links keep working on phones.
- Rule: Xray-core CLI ≥26 → pinned hash in JSON; phone app → `allowInsecure=1` URI usually still parses, but core support varies (see Link param matrix in `xray-vless-server`; iOS core 1.2.19 rejected `fp=<hex>` with `unsupported fingerprint`).
- **VERIFIED 2026-08-10**: full E2E with a real pinned hash WORKS — HTTP 200 through the fake-SNI tunnel (VLESS+WS+TLS, self-signed CN=mab.etisalat.com.eg, client pinned `pinnedPeerCertSha256`). Method:
  1. `openssl x509 -in server.crt -noout -fingerprint -sha256` → `SHA256 Fingerprint=AA:BB:...`
  2. Strip colons, keep uppercase hex → `pinnedPeerCertSha256: "AABBCC..."` (lowercase also fine). Base64 NOT accepted; placeholder `"ignore"` rejected with `encoding/hex: invalid byte: U+0069 'i'`.
  3. Phone-app URIs: `allowInsecure=1` (vpnjantit-style, old cores) or `pcs=<sha256-hex>` (Xray ≥26 / new v2rayNG). **Do NOT use `fp=<hex>`** — `fp` is the uTLS ClientHello fingerprint param and rejects hashes (`unsupported fingerprint` on iOS v2ray 1.2.19.2209, 2026-08-11).
- Deprecation timeline: v26.1.23 added `pinnedPeerCertSha256` (allowInsecure warnings only); ~v26.1.31 allowInsecure became a hard config error; v26.2.6 announced auto-disable; forced off 2026-06-01 UTC. vpnjantit-style `allowInsecure=1` links break in updated clients — pin the fingerprint instead. Full timeline + 3 migration paths: `references/allowinsecure-deprecation.md`.

## Steps to deploy on Railway
1. Repo: Dockerfile (alpine, `wget` Xray-linux-64.zip latest → unzip to /usr/local/bin, COPY server.crt/server.key/xray-config.json to /etc/xray/, EXPOSE 8080, `CMD ["xray","run","-c","/etc/xray/config.json"]`); server config = VLESS+WS inbound port 8080, `tlsSettings.certificates[0]` with `certificateFile`/`keyFile`; self-signed cert `CN=mab.etisalat.com.eg` + matching SAN.
2. Deploy from GitHub → Railway; enable TCP Proxy on internal 8080; note `*.proxy.rlwy.net:PORT`.
3. Phone URI: `vless://UUID@<proxy.rlwy.net>:<port>?encryption=none&security=tls&sni=mab.etisalat.com.eg&insecure=1&allowInsecure=1&type=ws&host=mab.etisalat.com.eg&path=%2F<yourpath>#name` (works on cores that still honor insecure; see Link param matrix in `xray-vless-server` for alternatives)
4. ALWAYS verify locally before deploying (next section).

## Permanent cert strategy (do this — user zero-friction lesson)
Build-time cert generation (`openssl req` in Dockerfile RUN) re-generates on EVERY rebuild → fingerprint changes → every stored link with cert-pin dies after a redeploy. VERIFIED bad for this user ("i dont want it to be tiring" — a rebuild breaking his link = tiring).
- FIX: pre-generate the cert ONCE locally, commit `certs/server.crt` + `certs/server.key` to the repo, Dockerfile `COPY`s them (keep the openssl fallback only for fresh clones).
- Compute the fingerprint locally from the committed cert: `openssl x509 -in certs/server.crt -noout -fingerprint -sha256 | sed 's/.*=//' | tr -d ':'` → bake it into the README link as `pcs=<hex>` (NOT `fp=`) so the user NEVER runs a command. Precompute UUID + path too; leave exactly ONE placeholder (SERVER:PORT) in the link.
- Then the user's only manual step is the Railway dashboard click (TCP Proxy add) — hand them the ready link and a 30-second numbered checklist.

## Verify a live deployment / is TCP Proxy enabled? (no dashboard access)
- The app domain (`xray-railway-vpn-production-XXXX.up.railway.app`) is the HTTPS edge, NOT the proxy. TCP proxy lives on a SEPARATE `*.proxy.rlwy.net:PORT` domain.
- Probe the app host for open ports: only 80/443 open → TCP proxy NOT enabled (edge only). Scan quickly with a python socket connect loop (`timeout=1.5–2.5` per port) over common proxy ports — a slow port-scan loop timed out at 120s; keep the candidate list short and use a per-command `timeout 40`.
- `echo | openssl s_client -connect <app-domain>:443 -servername mab.etisalat.com.eg -brief` → cert `CN=*.up.railway.app` = edge TLS = fake SNI cannot work on 443. This confirms the user must enable TCP Proxy (dashboard click) before anything works; no API/CLI path found to enable it for them.

## Local E2E test (mandatory before deploy)
- Config references `/etc/xray/...` cert paths → copy certs there locally too, else: `failed to parse certificate > open /etc/xray/server.crt: no such file`.
- Start server: `./xray run -c xray-config.json` (background=true; health-check with the probe below).
- Probe: `echo | openssl s_client -connect 127.0.0.1:8080 -servername mab.etisalat.com.eg -brief` → TLS1.3 + CN=mab.etisalat.com.eg (verified).
- Start client: xray with socks inbound `127.0.0.1:10808` + vless outbound fake-SNI to 127.0.0.1:8080; then `curl -x socks5h://127.0.0.1:10808 http://example.com/ -w "%{http_code}"`.
- DON'T hand-roll VLESS protocol frames over raw sockets — my manual frame got `proxy/vless/encoding: invalid request version`; use the official client binary for authoritative E2E.

## Scratch storage rule
Never put heavy downloads (Xray zip ~21MB, APKs) under /data (500MB cap) — scratch/build to /opt/work (1.8TB overlay).

## References
- `references/railway-fake-sni.md` — full tested server/client configs, Dockerfile, probe outputs, Railway facts.