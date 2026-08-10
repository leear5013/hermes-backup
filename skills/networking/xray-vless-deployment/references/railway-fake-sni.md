# Railway fake-SNI VLESS — tested artifacts (2026-08-10)

Verified live in-session: Xray 26.3.27, self-signed cert CN=mab.etisalat.com.eg, local E2E:
TLS1.3 handshake with fake SNI ✓, WS upgrade 101 + VLESS session accepted ✓.
Full internet-flow E2E via client binary NOT completed (pinnedPeerCertSha256 path was being finished).

## Server config (xray-config.json, port 8080)
```json
{
  "log": { "loglevel": "warning" },
  "inbounds": [
    {
      "port": 8080,
      "listen": "0.0.0.0",
      "protocol": "vless",
      "settings": { "clients": [{ "id": "<UUID>" }], "decryption": "none" },
      "streamSettings": {
        "network": "ws",
        "security": "tls",
        "tlsSettings": {
          "certificates": [
            { "certificateFile": "/etc/xray/server.crt", "keyFile": "/etc/xray/server.key" }
          ]
        },
        "wsSettings": { "path": "/fhxkzop4vbll" }
      }
    }
  ],
  "outbounds": [ { "protocol": "freedom", "tag": "direct" } ]
}
```
NOTE: Xray logs `WebSocket transport (with ALPN http/1.1) is deprecated ... migrate to XHTTP H2 & H3` — warning only, works.

## Self-signed cert (server side — same command vpnjantit-style panels use)
```bash
openssl req -x509 -nodes -newkey rsa:2048 -keyout server.key -out server.crt \
  -days 3650 -subj "/CN=mab.etisalat.com.eg" \
  -addext "subjectAltName=DNS:mab.etisalat.com.eg"
```
Verified: `openssl s_client` with `-servername mab.etisalat.com.eg` → `subject=CN=mab.etisalat.com.eg issuer=CN=mab.etisalat.com.eg TLSv1.3 TLS_AES_128_GCM_SHA256`.

## Dockerfile (Railway)
```dockerfile
FROM alpine:latest
RUN apk add --no-cache wget unzip
RUN wget -O /tmp/xray.zip https://github.com/XTLS/Xray-core/releases/latest/download/Xray-linux-64.zip \
    && mkdir -p /usr/local/bin && unzip /tmp/xray.zip -d /usr/local/bin \
    && rm /tmp/xray.zip && chmod +x /usr/local/bin/xray
COPY xray-config.json /etc/xray/config.json
COPY server.crt /etc/xray/server.crt
COPY server.key /etc/xray/server.key
EXPOSE 8080
CMD ["/usr/local/bin/xray", "run", "-c", "/etc/xray/config.json"]
```

## Client config (Xray-core ≥26 CLI) — pinnedPeerCertSha256, NOT allowInsecure
```json
{
  "log": { "loglevel": "warning" },
  "inbounds": [ { "port": 10808, "listen": "127.0.0.1", "protocol": "socks", "settings": { "udp": true } } ],
  "outbounds": [
    { "protocol": "vless",
      "settings": { "vnext": [ { "address": "<server>", "port": 8080, "users": [ { "id": "<UUID>", "encryption": "none" } ] } ] },
      "streamSettings": { "network": "ws", "security": "tls",
        "tlsSettings": { "serverName": "mab.etisalat.com.eg", "pinnedPeerCertSha256": "<sha256-hex-of-server.crt>" },
        "wsSettings": { "path": "/fhxkzop4vbll", "headers": { "Host": "mab.etisalat.com.eg" } } } }
  ]
}
```
Get the pin from the served cert:
`openssl x509 -in server.crt -outform der | openssl dgst -sha256` (lowercase hex, no colons).

## Phone URI (v2rayNG/NekoBox/Streisand keep allowInsecure)
```
vless://<UUID>@<proxy.rlwy.net>:<port>?encryption=none&security=tls&sni=mab.etisalat.com.eg&insecure=1&allowInsecure=1&type=ws&host=mab.etisalat.com.eg&path=%2Ffhxkzop4vbll#railway-vpn
```

## Railway facts collected
- TCP proxy: Settings → Networking → TCP Proxy → internal port → assigned `*.proxy.rlwy.net:<random-port>`; L4 raw passthrough (edge does NOT terminate/route)
- HTTPS edge terminates TLS + SNI-routes → fake SNI impossible there (verified conceptually + official edge-networking docs)
- Custom domain on TCP proxy: CNAME → proxy hostname (NO port); keep Railway's port; Cloudflare grey-cloud only
- Docs raw markdown: append `.md` (Mintlify) e.g. https://docs.railway.com/networking/tcp-proxy.md
- Telegram MTProto proxy template proves TCP-proxy-on-443 pattern: https://railway.com/deploy/telegram-mtproto-proxy
- "Magic ports" (external 443 mapping) exist for HTTP/HTTPS, NOT mixable with TCP proxy
- Plans: TCP proxy available beyond Trial (random high port); internal 443 common for MTProto

## Verification probes
```bash
# fake-SNI support (host terminates TLS itself):
echo | openssl s_client -connect gr1.vpnjantit.com:10002 -servername mab.etisalat.com.eg -brief
# → CONNECTION ESTABLISHED, TLSv1.3, Peer certificate: CN=gr1.vpnjantit.com (verified)
```