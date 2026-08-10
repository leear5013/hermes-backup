# Xray `allowInsecure` deprecation — timeline & migration (2026)

Source: cuanmu.com blog post (2026-06-12) + 2dust/v2rayN discussion #9460 + issue #9435. Relevant to anyone self-hosting VLESS+TLS with self-signed or fake-SNI certs.

## Timeline (why "June 2026 outage" happened)
| Version | When | What changed |
|---|---|---|
| v26.1.23 | 2026-01-23 | `pinnedPeerCertSha256` introduced; `allowInsecure` only warns |
| ~v26.1.31 | Jan 2026 | `allowInsecure` became a HARD config error (refuses to start) |
| v26.2.6 | 2026-02-06 | Release notes: auto-disable scheduled for 2026-06-01 UTC |
| 2026-06-01 UTC | forced off | Any config containing `allowInsecure` fails to build |

Error text (exact):
```
The feature "allowInsecure" has been removed and migrated to "pinnedPeerCertSha256".
Please update your config(s) according to release note and documentation.
```

## Who is affected
- **Broken**: Xray-core (CLI / v2rayN / passwall etc.) + classic TLS + self-signed cert OR SNI mismatch OR fake SNI — i.e. exactly the vpnjantit-style setup, if the client core updated past v26.
- **Unaffected**: VLESS+Reality (no cert chain involved); mihomo/Clash.Meta (`skip-cert-verify` still supported, separate Go core); sing-box (`tls.insecure` still supported).

## Migration paths (3)
1. **Trusted cert** (Let's Encrypt etc.): just remove `allowInsecure` — cert validates normally.
2. **Self-signed / fake-SNI** (our case): **cert-fingerprint pinning** —
   ```json
   "tlsSettings": {
     "security": "tls",
     "serverName": "mab.etisalat.com.eg",
     "pinnedPeerCertSha256": "D7DEF97A2B961B5A14186647404BD72904A70A98BCEBDF24EF9744541ADF282F"
   }
   ```
   Get fingerprint: `openssl x509 -in server.crt -noout -fingerprint -sha256` → strip colons. Multiple comma-separated allowed, any match passes. Field name is exactly `pinnedPeerCertSha256` (C + Sha256 caps, singular) — the older `pinnedPeerCertificateChainSha256` / `pinnedPeerCertificatePublicKeySha256` were removed too. It hashes the WHOLE cert (same value crt.sh / Chrome shows), not public key.
3. **Reality** — no cert at all; strongest anti-DPI; server-side rebuild required.

## VLESS URI format for pinned fingerprint (phone apps)
Modern clients (v2rayNG ≥ build, NekoBox, Streisand, Hiddify) accept the `fp` query param:
```
vless://UUID@host:port?encryption=none&security=tls&sni=mab.etisalat.com.eg&fp=HEXWITOUTCOLONS&type=ws&host=mab.etisalat.com.eg&path=%2Fxyz#name
```
`fp` = SHA-256 fingerprint of the server cert, colons stripped, uppercase.

## Verified E2E (2026-08-10, xray 26.3.27)
- Server: VLESS+WS inbound 8080, `tlsSettings.certificates` with self-signed `CN=mab.etisalat.com.eg` (+SAN same).
- Client: socks inbound 10808 + vless outbound, `serverName=mab.etisalat.com.eg`, `pinnedPeerCertSha256=<real hash>`.
- Result: `curl -x socks5h://127.0.0.1:10808 http://example.com/` → **HTTP 200**, egress confirmed via ipify.
- Failed placeholders: `"ignore"` → `encoding/hex: invalid byte: U+0069 'i'`; wrong format (base64) also rejected.

## Notes
- Server side never used allowInsecure — only the CLIENT config had it. Server `tlsSettings.certificates` with self-signed files remains fine.
- WS transport deprecation warning in xray logs ("migrate to XHTTP") is cosmetic — VLESS+WS still works (vpnjantit uses it).