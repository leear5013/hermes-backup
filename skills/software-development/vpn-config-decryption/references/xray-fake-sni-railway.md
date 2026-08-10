# Fake-SNI VLESS+WS+TLS on Railway (with Xray 26 pinned-cert migration) — verified 2026-08-10

Goal (Hesham, session 2026-08-10): the user runs Xray on Railway and wants the vpnjantit-style
shareable URI where `sni=mab.etisalat.com.eg` makes ISP DPI believe the TLS stream is Etisalat
browsing traffic. Everything below was verified LIVE this session, server + client, E2E
(HTTP 200 through the tunnel).

## 1. Why fake-SNI can't go through Railway's default edge
Railway's HTTPS edge (`*.up.railway.app`) terminates TLS itself and routes on SNI/Host —
`mab.etisalat.com.eg` is rejected before Xray ever sees bytes. `insecure=1` doesn't help because
the mismatch isn't at the client's cert check; it's at the edge's SNI routing.
**Fix: Railway TCP Proxy = Layer-4 raw passthrough** (docs.railway.com/networking/tcp-proxy; the
Telegram-MTProto template at railway.com/deploy/telegram-mtproto-proxy is the canonical example —
internal port 443, public random `*.proxy.rlwy.net:<port>`). No edge TLS → the server itself (Xray)
terminates TLS. Also: Railway supports both HTTP + TCP on one service; TCP Proxy port is
auto-assigned (random high port); custom domain works via CNAME → proxy.rlwy.net (grey-cloud only
behind Cloudflare).

## 2. Server side (Xray config, self-signed TLS inside)
Generate: `openssl req -x509 -nodes -newkey rsa:2048 -keyout server.key -out server.crt -days 3650 -subj "/CN=mab.etisalat.com.eg" -addext "subjectAltName=DNS:mab.etisalat.com.eg"`.

xray-config.json (inbound; path chosen to look innocuous):
```json
{
  "inbounds": [{
    "port": 8080, "listen": "0.0.0.0", "protocol": "vless",
    "settings": { "clients": [ { "id": "<uuid>" } ], "decryption": "none" },
    "streamSettings": {
      "network": "ws", "security": "tls",
      "tlsSettings": { "certificates": [ { "certificateFile": "/etc/xray/server.crt", "keyFile": "/etc/xray/server.key" } ] },
      "wsSettings": { "path": "/fhxkzop4vbll" }
    }
  }],
  "outbounds": [ { "protocol": "freedom", "tag": "direct" } ]
}
```
Client link (vpnjantit-style): `vless://<uuid>@<your-tcp-proxy-host>:<port>?encryption=none&security=tls&sni=mab.etisalat.com.eg&insecure=1&allowInsecure=1&type=ws&host=mab.etisalat.com.eg&path=%2Ffhxkzop4vbll#railway-vpn`

## 3. CLIENTS < 2026-06 shipped allowInsecure=1 → those links die.
**Xray-core forced `allowInsecure` offline 2026-06-01 UTC** (v26.1.23 adds `pinnedPeerCertSha256`
with warning; ~v26.1.31 hard-errors on `allowInsecure`; v26.2.6 announces the force date).
Error text verbatim: `The feature "allowInsecure" has been removed and migrated to "pinnedPeerCertSha256". Please update your config(s)...`
- Affected: traditional-TLS nodes that skip verify (self-signed / SNI mismatch). NOT affected:
  VLESS+Reality, sing-box, mihomo/Clash (`skip-cert-verify`), trusted-cert nodes.
- Malformed pin string fails JSON-load with `encoding/hex: invalid byte: U+0069 'i'` (e.g. setting `"ignore"`).

## 4. Working client config (Xray 26.3.27) — pinned fingerprint
```json
{
  "inbounds": [ { "port": 10808, "listen": "127.0.0.1", "protocol": "socks", "settings": { "udp": true } } ],
  "outbounds": [ {
    "protocol": "vless",
    "settings": { "vnext": [ { "address": "127.0.0.1", "port": 8080, "users": [ { "id": "<uuid>", "encryption": "none" } ] } ] },
    "streamSettings": { "network": "ws", "security": "tls",
      "tlsSettings": { "serverName": "mab.etisalat.com.eg", "pinnedPeerCertSha256": "<cert-sha256-hex-nocolons-uppercase>" },
      "wsSettings": { "path": "/fhxkzop4vbll", "headers": { "Host": "mab.etisalat.com.eg" } } }
  } ]
}
```
Get the pin: `openssl x509 -in server.crt -noout -fingerprint -sha256` → strip `:` → uppercase.
It IS the full cert SHA-256 (matches crt.sh / Chrome viewer), NOT the pubkey — the legacy
`pinnedPeerCertificate(Chain|PublicKey)Sha256` fields were also removed. Only the full-cert option remains.

## 5. Local E2E verification recipe (ran on this VPS, all passed)
1. `xray run -c xray-config.json` (certs must exist at the configured path; ran as root, `/etc/xray/`)
2. `echo | openssl s_client -connect 127.0.0.1:8080 -servername mab.etisalat.com.eg -brief` →
   `CN=mab.etisalat.com.eg` presented, TLSv1.3. Good.
3. Raw VLESS probe (no client needed): TLS-wrap socket to 127.0.0.1:8080 with
   `server_hostname="mab.etisalat.com.eg"` (`ssl.CERT_NONE`), send WS upgrade
   `GET /fhxkzop4vbll HTTP/1.1`, headers `Connection: Upgrade`, `Upgrade: websocket`,
   `Sec-WebSocket-Key: <b64>`, `Sec-WebSocket-Version: 13`, `Sec-WebSocket-Protocol: <base64("vless://<uuid>@127.0.0.1:8080")>`
   → expect `HTTP/1.1 101 Switching Protocols`.
4. Full client: second Xray instance as socks inbound → outbound vless→`127.0.0.1:8080` with the
   pinned-cert tlsSettings → `curl -x socks5h://127.0.0.1:10808 http://example.com/` → **HTTP 200, ~0.18s**.
   (Hand-rolled VLESS frames failed with `invalid request version` — don't hand-roll; use the real client.)

## 6. Current dead-end / UX gap
A vless:// URI param for `pinnedPeerCertSha256` doesn't exist yet in the share-link ecosystem the
user's apps accept — so the deliverable needs the cert fingerprint as a manual extra step in the app
(and the shareable raw link is the legacy `allowInsecure=1` form that newer cores reject).
Watch Xray release notes for a URI-param addition; until then, pinning must be configured per-client.