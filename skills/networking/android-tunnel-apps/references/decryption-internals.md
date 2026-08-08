# Decryption Internals — NPV Tunnel, HTTP Custom, HTTP Injector

Source: github.com/zhgddm/npv- (HABIBI + NullptrO), MIT, verified loading in the gateway venv 2026-08-08.
All scripts expose `run(file_bytes: bytes) -> Optional[str]` → indented JSON of the decrypted config.

## NPV Tunnel (NPVTUNNEL.py — standalone, NO external deps)

File anatomy:
- TEXT config file, optional header `NPVTSUB1` or `NPVT1` (stripped first 8/5 chars)
- Body split on `,` → payloads[]
- `payloads[1]` = base64 → `decrypt_logic` → JSON (first element if array)

Cipher internals (whitebox):
- `_WHITEBOX_BLOB` = base64 → gzip → pickle tuple of 4 lists:
  - p2: S-box/T-table lookup structure (nested list of uint32s — the core whitebox tables)
  - p3: per-round permutation tables
  - p4: final substitution layer
  - p5: second-round tables
- `whitebox_encrypt_block(block, p2, p3, p4, p5)`: 2-round SPN — state permutation
  `[0,5,10,15,4,9,14,3,8,13,2,7,12,1,6,11]`, nibble-wise table lookups (hi/lo split at
  `28 - row*8` / `24 - row*8`), final p4 substitution.
- `decrypt_logic`: IV-counter stream mode — first 16 bytes = IV, then per 16-byte block:
  encrypt IV via whitebox → XOR keystream into ciphertext; increment IV big-endian-ish
  (bytewise carry from the end).
- Output: JSON config (with header comment "HABIBIxNULLPTRO NPVT SCRIPT").

Note: it's a CUSTOM cipher, not AES — reverse-engineering further is unnecessary since the
script ships the full whitebox state and runs as-is.

## HTTP Custom (HTTPCUSTOM.py — needs `pip install pycryptodome`)

Constants:
- `CHACHA_KEYS`: 8 hardcoded 32-byte keys (try each until padding/UTF-8 validates)
- `RST_KEYS`: 9 AES keys as strings: JN1k3YHc2.6_v235, JN1k3YHc_2.7_v71, JN1k3YHc2.7.ps69,
  JN1k3YHc2.7.6950, Jn1K3yHc2.8.ps08, Jn1K3yHc2.9.ps6c, Zk:L7>WKaiK*s9>D, !<f!&WIlM**R.B0X, b4a5opinx2uloec6
- `JKL_KEY_OLD` / `JKL_KEY_NEW`: 20-byte XOR key variants
- `STATIC_NONCE` = b'\xdb' * 8 (ChaCha20), `RST_XOR_KEY` = bytes(range(2, 22))
- `BRAILLE_ALPHABET` for braille-encoded fields (index pairs → bytes)

Field decryption chain (per TOKEN_MAP field):
1. `_clean_hex` — strip non-hex, odd-length pad with leading 0
2. If hex string ≥ 32 chars → candidate bytes
3. ChaCha20 with each CHACHA_KEYS, nonce `\xdb`*8, `cipher.seek(64)`, decrypt `data[:-16]`
4. RST: XOR bytes with RST_XOR_KEY → base64 → AES-ECB decrypt with each RST_KEYS, unpad,
   accept if contains `[splitConfig]`
5. JKL: base64 → byte-wise bit-shuffle XOR `(((d^0xff)&0xca)|(d&0x35)) ^ (((k^0xff)&0xca)|(k&0x35))`
   → base64 again → UTF-8
6. Z3A: regex `(-?\d+)\.(-?\d+)` pairs → subtract IV → `(val11 // (1 << val22)) % 256` → bytes
7. Credentials `user:pass@...` via Z3A on each part; SSH creds may be braille-encrypted first

TOKEN_MAP (field id → meaning): 0=payload, 1=proxy, 2=lockAllConfig, 3=blockedByRoot,
4=expiryTime, 5=noteEnabled, 6=notes, 7=sshField, 8=mobileDataAndLockProvider,
9=unlockUserAndPass, 10=ovpnConfig, 11=ovpnUserAndPass, 12=sni, 13=unlockUserAndPass2,
14=unknown14, 15=blockedByHwid, 16=cloudconfig, 17=psiphon, 18=name, 19=blockArea,
20=connectionMode, 21=blockedByPassword, 22=unknown22, 23=extraSniffer, 24=psiphon2,
25=v2rayEnabled, 26=v2rayConfig, 27=version, 28=slowdnsEnabled, 29=slowdnsServer,
30=slowdnsPublickey, 31=dnsResolver

## HTTP Injector (.ehi — HTTPINJECTOR.py, needs argon2-cffi + msgpack)

Layers (from repo README):
1. Binary .ehi container: length-prefixed UTF-8 structure → encrypted payload
2. AES-CBC Layer 1: multiple IVs (bypass & standard sets), static AES-256 key → unpad
3. Colon-split: second part (base64) → AES-128 static key → garbage bytes
4. XXTEA decrypt with hardcoded master key → JSON string + configSalt
5. If advanced lock (standard IV): XOR configData with salt; Argon2 key from
   MasterKey (SHA-256 of config fields) + salt → ChaCha20-Poly1305 decrypt
6. Recursive inner field decoding: configMessage Java-UTF-16 XOR, embedded JSON in
   v2rRawJson / overwriteServerData

## Dark Tunnel / SSC Custom
Same repo has DARKTUNNEL.py (msgpack) and SSCCUSTOM.py — same `run()` contract.
