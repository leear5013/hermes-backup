# HTTP Injector cloud-config — Session 15 (2026-08-10): scan window downloads + brute-force pitfalls

Context: hunting the server-side `CONFIG_AES_KEY` for `POST https://www.ehiapp.com/httpinjector/config` (blob = 16B IV + AES-CBC ct). Sessions 13-14 established: cloud feature absent in 5.7.0, present in 6.4/6.5 (packed), packer timeline starts by 6.3.6 (DexProtector). Real-dex window: **5.8.1 → 6.3.5**.

## What happened this session

### 1. Blob re-fetch confirms PER-REQUEST encryption (repeat of session-13 finding)
- Same share code `ed242a7S` fetched again → blob now **624 B** (was 592 B), different IV (`3bf53c0e…` vs earlier `51b0c861…`).
- → random IV per fetch, static key. Ciphertext length 608 = 38 AES blocks, multiples of 16 confirmed.
- Blob re-fetch recipe (urllib, works from this VPS): `POST https://www.ehiapp.com/httpinjector/config`, header `X-Platform: android`, body `{"key":"ed242a7S"}`, UA `Evozi-EHI/1.4.1` → `{"code":200,"data":"<b64>"}`.

### 2. Exhaustive candidate-key sweep — ZERO hits (definitive)
- **2,253 candidate keys**: every printable dex string 8–64 chars + hex32/hex64 + `sha256(str)[:16]` of config-ish strings, from BOTH `/opt/work/old_classes.dex` (2017) and `/opt/work/ehi531_classes.dex` (5.3.1).
- × 7 IVs (blobIV, zero, 6 fixed .ehi IVs) × 2 layouts (`blob[16:]`, whole blob) × AES-CBC.
- Hit detection: `.ehi` magic (`\x00\x03ehi`) OR printable-ratio > 0.9. **Zero hits** → server key not in those dexes (expected: 2017 = pre-cloud, 5.3.1 = no cloud strings at all).

### 3. FALSE-POSITIVE PITFALL — "looks like JSON?" detector
- A hit-check that only tests `'{' in pt[:200] and '}' in pt[:200]` fired **93 times** on the sweep — all random binary (any 200 random bytes contain both bytes ~98% of the time).
- **Correct validation**: printable-ratio > 0.9 over first 80+ bytes AND strict `json.loads` on a slice, or `.ehi` magic prefix. Never rely on brace presence alone.

### 4. `basxIW…` near-baseUrl string — DISPROVEN as key
- `basxIWwUdkqjCj33WkHPX1XLcRlnz9UL` sits adjacent to `baseUrl` in the 5.7.0 dex string pool (~offset 889043). Tested as AES-256 key × 3 IVs × 2 layouts → garbage.
- **Lesson**: dex string pools are SORTED ALPHABETICALLY — string adjacency means nothing. 32-char random alphanumerics near crypto words are random identifiers, not keys. Don't chase them.

### 5. APK downloads completed (the actual next-session state)
Downloaded via the session-14 androidapks.com dl-link method (regex `6\.\d\.\d` in the old-versions HTML, grab nearest `https://dl.androidapksfree.net/file/<20-hex>?e=<epoch>&s=<40-hex>` within ±300 chars):

| file | version | size | magic |
|---|---|---|---|
| `/opt/work/ehi620.apk` | 6.2.0 | 34,004,338 | `PK\x03\x04` ✓ |
| `/opt/work/ehi611.apk` | 6.1.1 | 33,271,851 | `PK\x03\x04` ✓ |
| `/opt/work/ehi600.apk` | 6.0.0 | 28,458,442 | `PK\x03\x04` ✓ |

**UNSCANNED — next session continues here.** Scan order: 6.2.0 → 6.1.1 → 6.0.0. For each:
1. `zipfile` → list dex files; check sizes — **classes.dex ≥4MB = real dex** (like 5.7.0's 6.3MB), ~1-2MB = packer stub (like 6.3.6's 1.69MB) → if stub, try `assets/` for a second dex + `lib/*/libevozi*.so`/`libtunnelcore.so` string scan, then move on.
2. Regex-scan combined dex for: `CONFIG_AES_KEY`, `OLD_CONFIG_AES_KEY`, `IOS_CONFIG_AES_KEY`, `Evozi-EHI`, `ehiapp`, `httpinjector`, `config.ehi`, `EncryptedApi`, `attest_config`, `configSalt`, `EVZJNI`.
3. If any key-constant found: grab 32/64-hex strings NEAR the constant (but remember pitfall #4 — validate by actual decryption, not proximity).
4. Validate candidate keys by decrypting a FRESH blob fetch (blob changes per request, key stable) with `AES.new(k, AES.MODE_CBC, blob[:16]).decrypt(blob[16:])` → check `.ehi` magic or strict JSON parse.

## Working files
- `/opt/work/ehi_decrypt.py` — complete verified .ehi decryptor (matches `scripts/ehi_full_decrypt.py`; the local copy also carries the debug prints variant `/opt/work/debug_mac.py`).
- `/opt/work/cloud_brute.py` — the 2,253-key sweep (keep for re-runs; fix the JSON-detector per pitfall #3).
- `/opt/work/test_basx_key.py` — candidate-key harness template (clean to reuse).
- `/opt/work/fetch_blob.py` — blob re-fetch.
- `/opt/work/ehi636.apk` (packed), `/opt/work/ehi570.apk` (real dex, no cloud), `/opt/work/ehi531.apk` + `old_ehi.apk` (no cloud) — all scanned, don't re-scan.

## Status
- Cloud API blob key: **NOT recovered**. Remaining real-dex candidates: 6.2.0, 6.1.1, 6.0.0 (downloaded), then 5.8.1 (need download).
- If 6.0–6.2 scans come up empty too: the AES-blob feature may be 6.3-only (packed) → fall back to Frida/memory-dump/MITM paths, or reconsider whether the blob layer needs attestation first.
