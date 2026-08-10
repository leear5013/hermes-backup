# Railway fake-SNI VLESS build (Xray) — verified facts 2026-08-10

Goal (Hesham, `leear5013/xray-railway-vpn`): own VLESS server on Railway whose link matches
vpnjantit's shape: `security=tls&sni=mab.etisalat.com.eg&allowInsecure=1&type=ws&host=mab.etisalat.com.eg&path=%2F<p>`.

## Why the HTTPS edge can't fake-SNI (verified live)
- vpnjantit `gr1.vpnjantit.com:10002` = raw TCP, server terminates TLS itself.
  `openssl s_client -connect gr1.vpnjantit.com:10002 -servername mab.etisalat.com.eg -brief`
  → handshake OK, peer presents `CN=gr1.vpnjantit.com` (server ignores the ClientHello SNI;
  client forgives the mismatch via `allowInsecure=1`). Traffic NEVER touches mab.etisalat.com.eg —
  SNI is a DPI allow-word only.
- Railway's HTTPS edge validates SNI against your app domain → `sni=mab.etisalat.com.eg` is rejected
  before Xray sees the bytes. `insecure=1` can't help: there is no end-to-end TLS handshake for the
  client to skip verifying.
- Probe ANY candidate host before promising a fake-SNI link: `scripts/tls-sni-probe.sh`.

## Verified Railway TCP Proxy facts (docs.railway.com/networking/tcp-proxy, fetched 2026-08-10)
- Settings → Networking → TCP Proxy → enter the internal port → Railway generates a public
  `something.proxy.rlwy.net:<random-port>`; all traffic there is proxied L4 to the service.
- Load balancing: random across replicas in closest region.
- Custom domain: CNAME `db.example.com` → `something.proxy.rlwy.net` (WITHOUT the port), but you
  MUST still connect with Railway's proxy port. Cloudflare must be grey-cloud (DNS only).
  Hostname-validating clients may fail over custom domains — irrelevant here (our clients
  skip validation via allowInsecure).
- HTTP edge and TCP proxy can coexist on one service.
- OPEN at build time: plan/port constraints (Hobby vs Pro, allowed port range) — verify in the doc.

## Build recipe
1. Xray inbound: `vless` + `streamSettings.security: tls` + `certificateFile`/`keyFile` with a
   SELF-SIGNED cert (client skips validation anyway):
   `openssl req -x509 -newkey rsa:2048 -nodes -days 3650 -keyout key.pem -out cert.pem -subj "/CN=mab.etisalat.com.eg"`
   Keep `network: ws` + a ws path.
2. Dockerfile: COPY the certs into the image (or embed via entrypoint).
3. Deploy per repo README (alpine + Xray release zip + config → `xray run -c`), then
   Settings → Networking → TCP Proxy on the Xray listen port.
4. Client link:
   `vless://<uuid>@<host>:<railway-proxy-port>?encryption=none&security=tls&sni=mab.etisalat.com.eg&allowInsecure=1&insecure=1&type=ws&host=mab.etisalat.com.eg&path=%2F<p>#name`
   (`<host>` = the generated proxy domain or your CNAME; port = Railway's assigned proxy port, NOT 443).
- Verify before distributing: `openssl s_client -connect <host>:<port> -servername mab.etisalat.com.eg -brief`
  must handshake and present YOUR self-signed cert.