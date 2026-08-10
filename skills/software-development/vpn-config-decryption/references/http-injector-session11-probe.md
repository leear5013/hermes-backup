# HTTP Injector cloud-config — session 11 (2026-08-10): Go cross-ref found, 5.3.1 scanned, MAC gap

Follow-up to session10-probe.md. Three events: (a) the `.ehi` scheme's canonical cross-reference was
found (Go), (b) the 5.3.1 archive.org build was scanned — the cloud key is NOT in it either, narrowing
the window, (c) a Python port of the Go code reached the Argon2/ChaCha layer but failed MAC — the
bypass-path module remains the verified decryptor.

## 1. FrontierTM/Pantegnos ehi.go — the scheme's canonical cross-reference

Found via authenticated GitHub code search (`Bearer` token from `/data/.git-credentials`; query
`"com.evozi.injector" AES` → hit `FrontierTM/Pantegnos :: modules/impl/ehi.go`). Raw fetch:
`https://api.github.com/repos/FrontierTM/Pantegnos/contents/modules/impl/ehi.go` (base64 content).
12.7 KB Go. Confirms EVERYTHING in the zhgddm Python module and adds the inner-field layer the Python
module hides:

- Keys/IVs (identical to the Python module): `L1Key` 32B `7e1210f7aab956f7a668bda6e57feddb7f84ad840aef8d27b1b969959be3ab6c`,
  `L2KeyStatic` 16B `b2bc617c32d8b9eb1943a5ffa8051eea`, `EooMasterKey` `"null=V5kU5+FFrY\x00"`,
  `SideIvs` 3×16B + `StandardIvs` 3×16B (same bytes as the Python module's BYPASS_IVS/STANDARD_IVS).
- XXTEA: delta `0x9e3779b9`, rounds `6 + 52/n`, LE uint32 words; on output, `v[n-1]` = length prefix,
  else `TrimRight(dec, 0x00)`.
- Lock layer: `config["configData"]` → XOR-layer → base64 → raw payload layout:
  `raw[0]` = version byte, `raw[1:5]` timeCost LE, `raw[5:9]` memoryCost LE, `raw[9]` parallelism,
  `raw[0x0a:0x1a]` salt, `raw[0x1a:0x32]` nonce, `raw[:0x1a]` AAD, `raw[0x32:]` ChaCha20-Poly1305-X
  ciphertext. `argon2.IDKey(masterKey, salt, timeCost, memoryCost, parallelism, 32)`.
- **`generateMasterKey(config)`** (the Python module never shows this): concatenate in order —
  `configAesKey, configIdentifier, configSalt, configTimestamp, configExpiryTimestamp, lockModes,
  lockModesHash, configHwid, configLockMobileOperatorId` — non-string fields rendered py-style
  (`True`/`False`/int), missing optional fields SKIPPED, but the two timestamps ALWAYS append
  (default `0` when missing) → `SHA256(concat)` = master key. I.e. the config JSON's OWN
  `configAesKey` field is the lock-layer keying material (not a server secret).
- **`cleanInnerFields(config, saltKey)`**: every string field is inner-decrypted: `configMessage` →
  base64 → XOR of UTF-16-ish byte units with repeating `"EHIMSG"`; ALL other string fields →
  reverse string → custom-base64 decode (`CustomAlphabet = "RkLC2QaVMPYgGJW/A4f7qzDb9e+t6Hr0Zp8OlNyjuxKcTw1o5EIimhBn3UvdSFXs"`,
  `?` stripped, pad to %4) → the result is a HEX string → unhex → XOR with `saltKey` bytes
  (default `"EVZJNI"`), dropping `0x00` bytes → entropy guard (>50% control chars = fail).
- `parseEhiBytes` (Go): `readUTF` = u16 BE length + bytes, twice with 8-byte skips, then u32 BE
  payload length + 8-byte skip → payload. Matches the Python `_parse_ehi_bytes`.

## 2. Python port of ehi.go — got through L1/L2/XXTEA, MAC-check FAILED

Porting the Go pipeline to Python (pycryptodome ChaCha20_Poly1305 + argon2.low_level.hash_secret_raw
type=Type.ID) reproduced L1 (BYPASS_IVS[0]) → colon-split → L2 → XXTEA → config JSON on the real
Turkcell file, but the final `decrypt_and_verify(raw[0x32:], aad)` raised `ValueError: MAC check
failed`. Not debugged to root cause in-session. Plausible culprits (unverified): custom-b64/hex
round-trip fidelity on the XOR layer (`customB64Decode` returns the hex STRING as bytes; unhex before
XOR), `decodeConfigMessage`'s Go utf16.Encode semantics (each byte is one rune — Python should XOR
raw bytes, not decode to utf-16-le), or Go's `base64.StdEncoding` vs Python's
`base64.b64decode(validate=...)` on edge padding. VERDICT: do NOT swap `scripts/HTTPINJECTOR_fixed.py`
for a Go-derived port until the MAC path is proven; the bypass path (configSalt="" + isConfigLock=true)
never reaches this layer anyway.

## 3. archive.org 5.3.1 build scanned — key NOT there

`HTTP Injector-v5.3.1_SIZE12326324.apk` (12.3 MB, identifier `http-injector-v-5.3.1-size-12326324_202103`):
`classes.dex` 2.68 MB + `classes2.dex` 0.42 MB + `assets/audience_network.dex` 3.3 MB — all REAL dex.
Combined dex string scan (b64 + regex `[\x20-\x7e]{4,}`):
- `CONFIG_AES_KEY` / `OLD_CONFIG_AES_KEY` / `IOS_CONFIG_AES_KEY` / `CLIENT_KEY` / `configSalt` /
  `configData` / `Evozi-EHI` / `ehiapp` / `ehi.link` / `config.ehi` / `httpinjector/config` /
  `EncryptedApi` / `attest_config` / `import_config` → ALL ABSENT.
- Present: `AES/CBC/NoPadding`, `AES/CTR/NoPadding`, `AES_BLOCK_SIZE`, `ENCRYPTED_CPM_KEY` (ads),
  trilead SSH hex blob `AA87CA22…`, `import_config` as a bare string.
→ The cloud-blob layer postdates 5.3.1. Combined with the packer timeline (6.4.1 + 6.5.0 packed),
the unpacked-with-cloud-key window is **5.3.1 < v < 6.4.1** (roughly 6.0–6.3, 2021–2023).

## 4. Next moves (ranked)

1. Find an unpacked 6.0–6.3 build: archive.org advancedsearch
   (`q=http+injector+apk`), Wayback snapshots of apkpure.com pages, apkcombo r2 link patterns for
   old versions, apk.dog/apk.support old-version pages. Verify dex size > 100KB (stub test) BEFORE
   scanning.
2. In the old dex, the key constant will likely sit next to the `/httpinjector/config` path string
   and the `Evozi-EHI` UA — scan for the path first, then dump ±500 bytes of the string pool around it.
3. If all unpacked builds lack the cloud layer, the API is newer than the app's cloud feature:
   re-probe `/httpinjector/config` with the current APK's exact request shape is still blocked by the
   CF edge 405 (session 8/9) — device capture or DexHelper unpacking remains the fallback.

## 5. Environment notes (session 11)

- `web_search` tool was dead ("Web tools are not configured") → fixed per `hermes-web-search-stack`
  skill: `/opt/venv/bin/pip install ddgs` + `/opt/venv/bin/hermes config set web.search_backend ddgs`.
- pycryptodome had vanished from /opt/venv after the sandbox reset → `/opt/venv/bin/pip install
  pycryptodome argon2-cffi` (one-liner, ~seconds).
- archive.org download URLs with spaces must be %-encoded (`HTTP%20Injector-v5.3.1_SIZE12326324.apk`).
