---
name: android-tunnel-apps
description: NPV Tunnel, NetMod, HTTP Custom configs, vmess, decryption.
---

# Android Tunnel App Ecosystem (NPV / NetMod / HTTP Custom)

The Egyptian/PH community stack of Android "injector-style" tunnel apps, their config formats, and working decryption tooling. User (Hesham) works with these — needs deep knowledge AND working decryption, not just theory.

## When to use
- Questions about NPV Tunnel, NetMod, HTTP Custom, HA Tunnel, HTTP Injector, SSC Custom, Dark Tunnel
- `vmess://` / `nm-vmess://` / `vless://` / `trojan://` config strings
- Decrypting `.npv` / `.npv4` / `.inpv`, `.hc`, `.ehi` config files
- Building a config generator, decoder, or converter

## App family (all HTTP/HTTPS injector-style tunnel clients)
- **NPV Tunnel** — Android HTTP/HTTPS tunnel (Injector-style). Configs `.npv`/`.npv4`/`.inpv`: TEXT format, header `NPVTSUB1` or `NPVT1`, comma-separated fields; field[1] = base64 → whitebox-decrypt → JSON config.
- **NetMod** (NetMod Syna) — Windows + Android. Protocols: SSH, DNSTT, HTTP(S), SOCKS, VMess, VLESS, Trojan, Shadowsocks, OpenVPN, WireGuard. Own URI scheme **`nm-vmess://`** for importing VMess configs. Extra: payload generator, response replacer, host checker, private/encrypted locked configs.
- **HTTP Custom** — `.hc` binary configs; custom HTTP CONNECT payloads; can embed V2Ray config (`v2rayConfig` token).
- **HTTP Injector** — `.ehi` files; layered AES-CBC + AES-128 + XXTEA + Argon2 + ChaCha20-Poly1305.
- **HA Tunnel, Dark Tunnel, SSC Custom** — same family.

## Config formats
### vmess:// (V2Ray universal)
`base64(JSON)` → `{"v":"2","ps":"name","add":"host-or-ip","port":"443","id":"<uuid>","aid":"0","scy":"auto","net":"ws","type":"none","host":"cdn.example.com","path":"/ws","tls":"tls"}`. This is what makes vmess flexible — same server, many disguises.

### nm-vmess:// (NetMod variant)
NetMod's own prefix for VMess import — extends vmess with NetMod tunnel/payload settings. **BELONGS TO NETMOD, NOT NPV TUNNEL** (user correction 2026-08-08 — never mix up).

### NPV file
Text, comma-separated, `NPVTSUB1`/`NPVT1` header. Field[1] = base64 of whitebox-encrypted JSON (see references/decryption-internals.md).

### HTTP Custom .hc
Binary container; 32-field TOKEN_MAP (0=payload, 1=proxy, 12=sni, 25=v2rayEnabled, 26=v2rayConfig, 18=name, 4=expiryTime, ...) — full map in references/decryption-internals.md.

## Decryption tooling — zhgddm/npv- repo (VERIFIED WORKING)
Repo: `github.com/zhgddm/npv-` (branch `main`; MIT; Telegram t.me/habibidecodez). Files: `NPVTUNNEL.py`, `HTTPCUSTOM.py`, `HTTPINJECTOR.py`, `DARKTUNNEL.py`, `SSCCUSTOM.py`. Every script exposes `run(file_bytes: bytes) -> Optional[str]` returning the decrypted config as indented JSON.

```bash
curl -sL https://raw.githubusercontent.com/zhgddm/npv-/main/NPVTUNNEL.py -o /tmp/NPVTUNNEL.py
curl -sL https://raw.githubusercontent.com/zhgddm/npv-/main/HTTPCUSTOM.py -o /tmp/HTTPCUSTOM.py
# HTTPCUSTOM needs pycryptodome; HTTPINJECTOR needs argon2-cffi + msgpack:
/opt/venv/bin/pip install pycryptodome argon2-cffi msgpack
```
- **NPVTUNNEL.py** — fully standalone (whitebox tables embedded as base64→gzip→pickle blob; no deps). 2-round SPN whitebox cipher in IV-counter stream mode.
- **HTTPCUSTOM.py** — ChaCha20 (8 static keys, static nonce `\xdb`×8) + AES-ECB (9 RST keys) + JKL XOR + Braille + Z3A coordinate decoding.
- Verify: `run(b"garbage")` → `None` (graceful); real config → JSON text.

## Pitfalls
- **`nm-vmess://` is NetMod, NOT NPV Tunnel** — hard user correction, never repeat the mix-up.
- **`vmess://`/`nm-vmess://` strings are connection strings → REDACT ([REDACTED]) before persisting anywhere**, never log raw.
- **Storage: scratch/configs → /tmp (overlay, 1.8TB), never /data (500MB limit)** — user explicitly asked for this.
- `web_search_tool` returns a dict OR a JSON **string** — parse defensively (`json.loads` when `isinstance(r, str)`).
- Community knowledge lives on phcorner.org, r/vpngeeks, StackOverflow, YouTube (Russian-language NPV tutorials exist too). Reddit direct fetch is blocked from this VPS — use the `site:reddit.com` search → Arctic-Shift path.
- These apps are ISP-bypass tools; scripts are public/MIT and educational.

## Verification checklist
- [ ] NPVTUNNEL + HTTPCUSTOM import cleanly in the gateway venv
- [ ] `run()` returns indented JSON for a real config, `None` for garbage
- [ ] vmess:// decodes to the 13-field JSON schema above

## References
- `references/decryption-internals.md` — NPV whitebox structure + HTTP Custom crypto constants/token map + .ehi layer summary
