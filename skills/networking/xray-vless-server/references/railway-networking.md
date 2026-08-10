# Railway networking facts + vpnjantit probe transcript (2026-08-10)

Verified live from this environment. Sources: docs.railway.com raw `.md` pages, railway.com template page, openssl probes of gr1.vpnjantit.com.

## Edge vs TCP proxy (the two models)
- **Edge (= public domain, `.up.railway.app:443`)**: anycast → edge POP terminates TLS with its own cert → adds headers → routes on SNI/Host → forwards to deployment. TLS is terminated at the edge; it serves Railway's cert for your domain, so the client MUST use `sni=<your-app>.up.railway.app` and real cert validation works.
- **TCP Proxy**: Layer-4 passthrough. You configure only the INTERNAL port; Railway generates a public `*.proxy.rlwy.net:<random-port>`. No TLS termination, no HTTP headers (`X-Forwarded-For` noted absent for TCP by Railway staff), no hostname validation at the proxy — raw bytes pass through. Auth-required app-level facts: internal port you choose (e.g. 8080 for xray); can't choose the public port (random high port).
- MTProto template (`https://railway.com/deploy/telegram-mtproto-proxy`) uses exactly this: "Internal Port must be 443" + TCP Proxy → link `your-service.proxy.rlwy.net:12345`. Confirms the pattern is first-class on Railway.
- Railway template pages are JS-rendered; the `.md` markdown endpoint returns clean source (trafilatura "no usable text" on the HTML, scrapling Fetcher needed for the HTML but docs `<page>.md` gives raw markdown directly).

## Performance/plan notes
- Edge terminations happen at nearest edge POP; deployments run in 4 regions (US West/East, Europe West, Asia Southeast).
- TCP proxy load balances across replicas in closest region (random LB).
- Custom domain CNAME → proxy domain (port stays the Railway-provided one). Cloudflare must be grey-cloud (DNS only).

## vpnjantit probe transcript
```
$ getent hosts gr1.vpnjantit.com      → 51.195.91.135
$ getent hosts mab.etisalat.com.eg    → 41.222.129.178

TEST A: openssl s_client -connect gr1.vpnjantit.com:10002 -servername gr1.vpnjantit.com -brief
→ CONNECTION ESTABLISHED, TLSv1.3, TLS_AES_256_GCM_SHA384, Peer certificate: CN=gr1.vpnjantit.com, Verification: OK

TEST B: same but -servername mab.etisalat.com.eg
→ CONNECTION ESTABLISHED, TLSv1.3, same cipher, Peer certificate: CN=gr1.vpnjantit.com, Verification: OK
```
So the panel terminates TLS itself and ignores the requested SNI (serves its own cert) → client skips validation via allowInsecure. This is the reproducible model.

## The user's own repo (leear5013/xray-railway-vpn)
- Dockerfile: alpine, wget/unzip Xray-linux-64.zip → /usr/local/bin, `CMD xray run -c /etc/xray/config.json`, EXPOSE 8080.
- xray-config.json: vless on 8080, ws path /fhxkzop4vbll, NO tlsSettings (edge does the TLS).
- README link: `vless://4912317f-...@your-app.up.railway.app:443?...&sni=your-app.up.railway.app&type=ws&host=mab.etisalat.com.eg&path=%2Ffhxkzop4vbll#railway-vpn` — note it uses `host=mab.etisalat.com.eg` (WS Host header = cosmetic, server ignores) but `sni=your-app...` (REQUIRED for edge TLS).