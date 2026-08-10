# HTTP Injector cloud-config — Session 13 (2026-08-10) — key space exhausted, window narrowed

## Outcome in one line
The cloud-blob AES key is NOT any string/hex/hash in the 2017 or 5.3.1 dexes (2,253 keys × 7 IVs × 2 layouts = exhaustive, zero hits), the blob is per-request encrypted (different IV per fetch), and the next real lead is an APK in the **5.3.1 < v < 6.4 window** (APKMirror 6.2.0/6.2.1/6.3.0/6.3.1, androidapks 6.3.5/6.3.4, apk.dog 6.1.1).

## Background state at session start
- Cloud blob for `ed242a7S`: `POST https://www.ehiapp.com/httpinjector/config`, header `X-Platform: android`, body `{"key":"<code>"}` → `{"code":200,"data":"<b64>"}` → 16-byte IV + AES-CBC ciphertext.
- `.ehi` local-file decryption **fully solved** (see `references/http-injector-session12-probe.md` and `scripts/ehi_full_decrypt.py`) — not the blocker.
- The blocker is the *server-side* `CONFIG_AES_KEY` value, believed to live in the DexHelper-encrypted dex of current (≥6.4.1) APKs.

## What was tried (exhaustive, all failed → useful negatives)

### 1. Full candidate-key brute force (2,253 keys)
Key space assembled from BOTH real-dex builds on disk:
- `/opt/work/old_classes.dex` (2017 `com.evozi.injector`, 5.0MB)
- `/opt/work/ehi531_classes.dex` (5.3.1, combined classes.dex+classes2.dex, 3.1MB)

Candidates:
- every printable string 8–64 chars (regex `[\x20-\x7e]{8,64}`) — 40,920 unique strings
- hex32 / hex64 runs (16B / 32B key candidates)
- sha256[:16] of any string containing injector/evozi/config
- known constants: L1Key, L2KeyStatic, EooMasterKey, `B3EEABB8EE11C2BE770B684D95219ECB`, `A79B9859F741E082542A385502F25DBF…` (first 16B), UA `Evozi-EHI/1.4.1`

IVs: blobIV, zero, 6 fixed .ehi IVs. Layouts: `blob[16:]` (IV stripped) AND whole blob.
Detection: readable text (>90% printable, >20B) OR `.ehi` magic (`\x00\x03ehi` / `\x00\x03EHI`), plus unpad-then-check.

**Result: ZERO hits.** → The key is not a plaintext string in either dex. Consistent with the key living in the DexHelper-encrypted payload of ≥6.4 builds, or being derived (e.g. SHA of a string) in the app's real code.

### 2. Blob is per-request encrypted
Fetching the SAME share code `ed242a7S` twice:
- fetch 1: 592 B, IV head `51b0c8617c1976a25bd6ec03b6e9c230` (session 12 data)
- fetch 2: 624 B, IV head `3bf53c0e796b8f73d5459a554aa15001`

→ IV AND ciphertext size vary per request (random IV, likely random padding too); the KEY is what's constant. A stored blob from a prior fetch is fine to test against (key is stable), but you can't rely on IV/size matching.

### 3. 5.3.1 dex cloud-feature scan (negative, confirms window)
5.3.1 combined dex has **ZERO** hits for: `httpinjector`, `cloud`, `config.ehi`, `ehi.link`, `ehiapp`, `/config`, `getconfig`, `import_config`, `Evozi-EHI`. Its only URLs are Google/Ad SDK ones (`https://app-measurement.com/a`, `https://pagead2.googlesyndication.com/...`, `https://firebaseremoteconfig.googleapis.com/...`). Its `AES/CBC/NoPadding` + `AES/CTR/NoPadding` + `ENCRYPTED_CPM_KEY` strings are the LOCAL .ehi scheme (same strings the 6.5.0 .so pool has) + ads. → **The cloud share-key feature is NOT in 5.3.1** (2021). It appeared somewhere in 5.4–6.3.x, before 6.4 packed the dex.

## Positive leads for next session (in order)

1. **APKMirror pre-packer builds** (real dex, unpacked era):
   - 6.2.0: `https://www.apkmirror.com/apk/evozi/http-injector/http-injector-6-2-0-release/` (2024-03-10/16, ~14.07 MB, SHA-1 `1d0b44fbedb3a550bffa94d4a344448ad4a6b063`)
   - 6.2.1, 6.3.0 (2024-04-08, ~14.36 MB, SHA-1 same family), 6.3.1 (2024-04-09)
   - APKMirror download is JS-gated from this VPS (`/download/?key=<40-hex>` → 302 HTML shell). Variant URLs like `.../http-injector-6-2-0-android-apk-download/` may need browser UA + referer; if blocked, try the mirrors below.
2. **androidapks.com** old-versions page `https://androidapks.com/http-injector/com-evozi-injector/old/` — lists 6.3.5 and 6.3.4 (direct-ish APK links, no JS gate historically).
3. **apk.dog** — `https://apk.dog/download?file_id=2748473/http-injector-ssh-proxy-vpn` (6.1.1 MOD listed), appteka `https://appteka.store/app/f1cr79614` (5.6.4), softpedia `https://mobile.softpedia.com/apk/http-injector/` (5.6.0).
4. Archive.org advancedsearch: `https://archive.org/advancedsearch.php?q=http+injector+apk&fl[]=identifier&rows=20&output=json` — only 2 identifiers found so far (`com.evozi.injector` 2017, `http-injector-v-5.3.1-size-12326324_202103`); try other query shapes (`evozi`, `httpinjector`).

**Scan recipe once a 6.x dex is in hand** (`scripts/scan-dex-strings.py` or inline):
- `CONFIG_AES_KEY` / `OLD_CONFIG_AES_KEY` / `IOS_CONFIG_AES_KEY` / `EncryptedApi` / `attest_config` / `Evozi-EHI` / `ehiapp` string hits
- hex32/hex64 runs near those strings in the string pool (the value may sit as a neighbor)
- if the dex is a ~22KB stub with `DexHelper`/`###ACFNAME###` → packed, skip (that's ≥6.4.1 behavior; the .so string-table technique in `references/http-injector-session8-probe.md` still applies for API paths but never yields the key VALUE).

## Useful negatives / don't redo
- The 2017 `com.evozi.injector` APK (5.5MB, archive.org) is pre-cloud: NO cloud/config strings beyond `import_config` (unrelated), `AES/CBC/PKCS5Padding` (Google ads `AESSettingsCipherMode`), no `Evozi-EHI`, no `/httpinjector`. Don't re-scan it for the key.
- 5.3.1: same verdict (above).
- The `A79B9859F741E082542A385502F25DBF55296C3A545E3872760AB7` hex near `AES/CBC/NoPadding` in 5.3.1 is a **trilead SSH ECDH constant**, not the AES key (already established in session-8 for 6.x; re-confirmed same string in 5.3.1 pool).
- A brute force over dex strings can never find the key if it's computed at runtime (e.g. `sha256(CONFIG_AES_KEY + salt)` or assembled in the packed dex). If the 6.2/6.3 dex yields nothing either, the remaining paths are Frida/objection runtime hook of `SecretKeySpec` / `Cipher.init` on a device, or MITM of a real in-app import.
