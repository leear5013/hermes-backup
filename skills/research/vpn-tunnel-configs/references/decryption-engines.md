# Decryption engine internals (verified 2026-08-08)

Source: `zhgddm/npv-` (GitHub, default branch `main`). Files: `NPVTUNNEL.py`, `HTTPCUSTOM.py`, `HTTPINJECTOR.py`, `DARKTUNNEL.py`, `SSCCUSTOM.py`. Repo README says all scripts expose `run(file_bytes: bytes) -> Optional[str]` → pretty-printed JSON.

## Install deps (into the GATEWAY venv — not system python)
```bash
/opt/venv/bin/pip install pycryptodome argon2-cffi msgpack
```

## NPV Tunnel (NPVTUNNEL.py) — whitebox SPN stream cipher
- Config file: ASCII text, header `NPVTSUB1` or `NPVT1` (stripped), then comma-separated payloads; `payloads[1]` is the base64 ciphertext.
- Decryption: `decrypt_logic(b64_payload, p2, p3, p4, p5)`:
  1. base64-decode → first 16 bytes = IV, rest = ciphertext.
  2. Keystream = `whitebox_encrypt_block(iv, ...)` — a custom 2-round SPN with a fixed byte-permutation `[0,5,10,15,4,9,14,3,8,13,2,7,12,1,6,11]` and lookup tables (p2/p3/p4/p5) loaded from a base64+gzip+pickle `_WHITEBOX_BLOB`.
  3. Runs in **IV-counter mode**: after each 16-byte block the IV increments (big-endian, no carry-out); ciphertext XOR keystream → UTF-8.
- Result: JSON string (list → first element returned).
- **Zero external deps** — the whitebox tables are embedded; module imports and `run()` work standalone.

## HTTP Custom (HTTPCUSTOM.py) — layered scheme
- `HCDecryptor` class; token map (config field IDs): 0 payload, 1 proxy, 2 lockAllConfig, 3 blockedByRoot, 4 expiryTime, 5 noteEnabled, 6 notes, 7 sshField, 8 mobileDataAndLockProvider, 9 unlockUserAndPass, 10 ovpnConfig, 11 ovpnUserAndPass, 12 sni, 15 blockedByHwid, 16 cloudconfig, 17 psiphon, 18 name, 19 blockArea, 20 connectionMode, 21 blockedByPassword, 23 extraSniffer, 24 psiphon2, 25 v2rayEnabled, 26 v2rayConfig, 27 version, 28 slowdnsEnabled, 29 slowdnsServer, 30 slowdnsPublickey, 31 dnsResolver.
- Primitives: `_decrypt_braille` (Braille-encoded chars → bytes), `_extract_z3a` (float-pair coordinate encoding), `_abc_decrypt` (ChaCha20, 8 static keys, seek(64), static 8-byte nonce, trailing 16-byte tag), `_rst_decrypt` (AES-ECB with 9 RST keys, PKCS7 unpad, expects `[splitConfig]`), `_jkl_decrypt` (base64 + byte-XOR with 20-byte JKL key, old/new variants), `_process_credentials` (user:pass decoding for SSH).
- Needs `Crypto` (pycryptodome). Tested import: OK after install.

## Verify both engines load
```python
import importlib.util
for path in ("/tmp/NPVTUNNEL.py", "/tmp/HTTPCUSTOM.py"):
    spec = importlib.util.spec_from_file_location("m", path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    print(path, "OK; run =", hasattr(m, "run"))
```

## Research paths that FAILED (don't repeat)
- GitHub code search API (`api.github.com/search/code`) — requires auth.
- grep.app — Vercel security checkpoint block.
- phcorner.org threads — login-walled; comments show in search snippets only.
- YouTube tutorial content — video-only, not extractable text.
- `raw.githubusercontent.com` 404s if you guess the wrong branch — query `default_branch` via the repos API first.
