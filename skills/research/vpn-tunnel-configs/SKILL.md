---
name: vpn-tunnel-configs
description: Use for VPN tunnel configs, vmess codes, or decryption.
---

# Android Tunnel/VPN Configs: Ecosystem, Formats, Decryption

Egyptian/PH community stack (user works in this space — decryption was an explicit requirement). Sources verified 2026-08-08 from a datacenter VPS.

## The apps

| App | What it is | Config formats |
|---|---|---|
| NPV Tunnel | Android HTTP/HTTPS tunnel (Injector-style) | `.npv` / `.npv4` / `.inpv`; header `NPVTSUB1` or `NPVT1`, comma-separated fields, field[1] = base64 ciphertext |
| NetMod (Syna) | Full VPN client + toolkit, Windows + Android | V2Ray/Xray import; own URI schemes `nm-vmess://`, `nm-vless://`, ... |
| HTTP Custom | Android HTTP injector | `.hc` / `.hjson`; encrypted binary profile with 32-field token map |

**Family logic:** HTTP(S) injectors that wrap traffic in ordinary-looking HTTP(S) requests to defeat ISP Deep Packet Inspection (Egyptian/PH "free internet" use case). The encrypted hop is VMess/SSH/SSL to a real server behind an innocent-looking host/SNI (CDN host etc.).

## vmess:// format (verified against official v2ray.com sample)
`vmess://` + **base64(JSON)** — no `@`/query parts. Decoded JSON fields:
- `v`: "2" (version) · `ps`: profile name · `add`: server host/IP · `port` · `id`: VMess UUID (client credential) · `aid`: alterId (0 = modern) · `scy`: security (auto/aes-128-gcm/chacha20-poly1305) · `net`: transport (tcp/ws/grpc/h2/kcp) · `type`: fake-header (none/http) · `host`: WS Host/SNI · `path`: WS path · `tls`: tls/none

## nm-vmess:// (NetMod's scheme — NOT NPV)
- **User correction (Aug 2026):** `nm-vmess://` belongs to **NetMod**, not NPV Tunnel.
- NetMod's own import scheme for V2Ray/VMess configs; can carry NetMod extras (payload, SNI, tunnel type, private/locked-profile flags) beyond standard vmess fields.
- Exact byte schema is **not publicly documented** — do NOT fabricate it. Ground-truth paths: decode a user-provided sample (redact credentials), or pull the NetMod APK and read its URI parser.

## Decryption tooling (working, tested)
GitHub `zhgddm/npv-` — public decryption scripts for HTTP Injector (`.ehi`), NPV Tunnel, HTTP Custom, Dark Tunnel, SSC Custom. Each exposes `run(file_bytes: bytes) -> Optional[str]` returning pretty JSON.
- Deps: `/opt/venv/bin/pip install pycryptodome argon2-cffi msgpack`
- NPVTUNNEL.py: zero deps (whitebox tables embedded). HTTPCUSTOM.py: needs pycryptodome.
- Crypto internals + verify snippet: `references/decryption-engines.md`

## Security rule
`vmess://` / `nm-vmess://` strings are **connection strings** — NEVER persist raw values; redact credentials ([REDACTED]) before storing anywhere (chat history, files, git).

## Sources
- zhgddm/npv- (GitHub decryption scripts; Telegram channel t.me/habibidecodez)
- netmodvpnclient.com, sourceforge.net/projects/netmodhttp (NetMod official)
- r/vpngeeks, phcorner.org (community config-creation threads)
