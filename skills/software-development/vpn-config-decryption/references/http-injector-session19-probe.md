# HTTP Injector cloud-key hunt — Session 19 (2026-08-10)

Goal: decrypt the share-key cloud blob (`POST https://www.ehiapp.com/httpinjector/config`, body `{"key":"<code>"}`, header `X-Platform: android`) → AES-128-CBC blob (first 16 B = IV, rest = ct). Needs server-side `CONFIG_AES_KEY`.

## State at session start
- Static key hunt "exhausted": 2,253 keys × 7 IVs × 2 layouts = 0 hits (session 13); 6.0/6.1.1/6.2.0/6.3.6/5.7.0 all scanned, cloud feature born packed at 6.3.2 (DexProtector); archive.org has only pre-cloud builds.
- Session 18 reopened: HTTP Injector Lite 5.3.1 (current build, versionCode 14221, compileSdk 33) is COMPLETELY UNPACKED and its string pool has the full cloud model.

## What was done this session (all verified)

### 1. Lite 5.3.1 cloud model confirmed + key obfuscation mechanism identified
- APK: `com.evozi.injector.lite-5.3.1.apk` (8,075,491 B) from apk.cafe signed download (`/go/?file_id=2357517&b=<base64url>`; b decodes to a filesincloud.com URL). NOTE: `file_id=2393980` under the lite slug actually served MAIN app 5.4.0 — trust the filename inside decoded `b`.
- Dex: `classes.dex` 8,248,004 B (real!) + `classes2.dex` 2,566,784 B. 16,810 classes total.
- String pool hits: `Lcom/evozi/injector/lite/model/EncryptedApi;`, `HttpObfs`, `IAP`, `News`, `Timestamp`, `Version`; fields `configIdentifier/configLock/configMessage/configSalt/configTimestamp`; URLs `https://www.ehi.tools/` + `https://www.ehiapp.com/`; paths `/httpinjectorlite/news|timestamp|version`; helper `AesCbcWithIntegrity` + `Unseal`.
- **`EncryptedApi` Gson fields:** `_encrypt`, `_decrypt`, `_encryptIV`, `_decryptIV`, `_encryptSaltSet`, `_decryptSaltSet` — the blob is an EncryptedApi JSON: salt set + IV + encrypted data (+ HMAC integrity via AesCbcWithIntegrity).
- **`AesCbcWithIntegrity` methods (obfuscated names, from androguard):**
  - `<clinit>` — builds static key strings from `const-wide` longs via deobfuscator (see below)
  - `ﾠ͏⁫(String, [B, I) → Params` (params builder)
  - `ﾠ⁪() → [B` — key-derivation output (bytes)
  - `ﾠ⁭(String, Params, String) → String` — decrypt
  - `ﾠ⁮(Params, Params, String) → String` — encrypt
  - `ﾠ⁬⁪([B, SecretKey) → [B` — AES block op
- **THE KEY MECHANISM (the important find):** `<clinit>` disassembly shows:
  ```
  const-wide v0, -78612227362228
  invoke-static v0, v1, Lcom/google/android/gms/internal/ﻢ;->ﾠ⁬͏(J)Ljava/lang/String;
  move-result-object v0
  sput-object v0, Lcom/evozi/injector/lite/helper/AesCbcWithIntegrity;->ﾠ⁬͏ Ljava/lang/String;
  const-wide v0, -78702421675444
  ...
  ```
  I.e. string literals are encoded as **negative long constants** and decoded by a long→String helper parked in the **Google gms namespace** (`com.google.android.gms.internal.ﻢ`) — Evozi's own obfuscator, not Google code. Class names like `ﻢ` (Arabic letter, 0x0622) are used as identifiers — UTF-8 class names in dex are fine.
- **Next step:** dump `ﻢ;->ﾠ⁬͏(J)Ljava/lang/String;` bytecode (it will be e.g. a char-by-char or chunked reconstruction from the long bits), decode the `<clinit>` longs → recover the AES password/salt/IV constants → decrypt Lite blobs; check whether the main app's blob shares the scheme (same `CONFIG_AES_KEY` family).

### 2. androguard 4.1.4 gotchas (all hit, all verified)
1. `APK(path_str)` — a `BufferedReader`/file object → `TypeError: expected str, bytes or os.PathLike object, not BufferedReader` (raised deep in apkInspector.headers.parse). Fix: pass the path string.
2. `DEX(bytes)` — a file object → `ValueError: This is not a DEX file! Wrong endian tag: '0x73656669'`. Fix: read with zipfile and pass `zf.read(name)` bytes. (`DEX` also can't take a CONCATENATION of two dexes — parse each dex entry separately.)
3. `code.get_bc().get_instructions()` returns a **generator** — `print(...)` prints `<generator object DCode.get_instructions at 0x...>`. Iterate: `for ins in bc.get_instructions(): print(ins.get_name(), ins.get_output())`.
4. androguard logs DEBUG to stderr on load (APK validation, dex parsing) — redirect output to a file and read it, don't pipe through head.

### 3. Dead ends re-confirmed this session
- **Share-code-derived keys** (24 combos: sha256/md5 of code with/without salts, code bytes zero-padded to 16/32, EooMasterKey ± code, sha256 of those, L1/L2 keys, md5(code)) → all invalid PKCS7. Server key is NOT `f(share_code)`.
- **32-char alphanumerics adjacent to crypto words in string pools** (e.g. `basxIWwUdkqjCj33WkHPX1XLcRlnz9UL` beside `baseUrl` in 5.7.0 dex): 93 "JSON?" false positives in a 2,253-key sweep are random binary — need printable-ratio > 0.9 AND strict json.loads. The dex string pool is alphabetically sorted, so adjacency means nothing.
- **APKMirror direct APK**: cookie+session-bound; `/download/?key=k1` page returns a ROTATED `k2`; `download.php?id=...&key=k2` needs the same cookie jar; stale keys 404. Chain works but is 3 hops; androidapks.com and apk.cafe are simpler.
- **6.3.6 from APKMirror (54,456,565 B)** is ALSO DexProtector-packed: stub `classes.dex` 1,693,476 B, `libdexprotector*.so`/`libdpboot.so`/`libol.so` present, NO `libdatajar.so`. Packing began by 6.3.6 (not 6.4 as earlier assumed).
- 6.2.0/6.1.1/6.0.0: all armeabi-v7a-only, DexProtector-packed, zero cloud strings (re-confirmed; `libdexprotector_h.so` = the hooked variant).
- 5.7.0 dex: real 10.6 MB, URLs list = only Google/FB/crashlytics SDK endpoints — no cloud.
- GH code search for `Evozi-EHI` / `libdatajar` / `IOS_CONFIG_AES_KEY` / `httpinjector/config`: 0 meaningful hits (`libdatajar` hits are APKiD yara rules, not the app).
- Lite 5.4.0 (from apk.cafe file_id=2393980): pre-cloud (that's the file_id/slug trap above).

## Files on disk (all /opt/work/)
- `ehi_lite531.apk` — the unpacked Lite 5.3.1 (key source of truth)
- `decompile_lite.py`, `decompile_lite2.py` + `decompile_lite_out.txt` / `decompile_lite2_out.txt` (710 lines of smali incl. `<clinit>` longs)
- `ehi636_am.apk` — APKMirror 6.3.6 (packed, confirmed)
- `ehi620.apk`, `ehi611.apk`, `ehi600.apk` — packed 6.x builds (scanned, dead)
- `ehi570_dex.bin` — 5.7.0 real dex (scanned, dead)
- `blob_ed242a7S.enc` — the target blob (624 B = 16 IV + 608 ct)
- `test_code_derived.py` — the 24-key share-code derivation test (0 hits)

## Next best moves (in order)
1. **Dump `ﻢ;->ﾠ⁬͏(J)Ljava/lang/String;`** from Lite classes.dex → implement long→String decoder in Python → decode all `AesCbcWithIntegrity.<clinit>` + `EncryptedApi`/`Constant` `<clinit>` longs → the Lite AES password/salt/IV constants.
2. If Lite blob scheme differs from main app's, check `Unseal` (reflection) usage — may unhide `EncryptedApi` hidden fields.
3. Then try Lite constants against the main-app blob; if no, the main app's constants are still only in the packed 6.3.2+ dex → Frida/rooted dump/MITM remains the fallback.
