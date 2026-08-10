# Session 18 (2026-08-10) — Lite 5.3.1 UNPACKED + cloud model found; share-code-key falsified

Cloud blob `ed242a7S` still locked (needs CONFIG_AES_KEY). This session closed more dead ends and found the new primary lead. Blob re-fetch confirmed per-request random IV again (624 B this time: 16B IV + 608B ct).

## Dead ends closed
- **Share-code-derived key FALSIFIED**: 24 keys tested with AES-CBC (blob IV, blob[16:] ct) — sha256/md5 of the code in 5 salt variants (empty/code/lower/upper), sha256(sha256), md5×2, raw code bytes padded to 16/32, EooMasterKey ± code, sha256(EooMaster), L1/L2 keys → NO valid PKCS7. The server key is NOT f(share code).
- **6.3.6 APKMirror build (54.4MB)** = DexProtector packed (same packer libs as the androidapks build: libdexprotector*.so/libdpboot.so/libol.so); zero cloud strings in 14.5MB of dex + 30 .so files. APKMirror chain (cookie jar + per-hop key re-extraction) works for downloads.
- **5.7.0**: real 10.6MB dex, but ZERO cloud-feature strings (no configSalt/EncryptedApi/ehiapp/cloud) — feature absent at 5.7.0.
- **6.2.0/6.1.1/6.0.0**: all DexProtector-packed (armeabi-v7a only), zero cloud strings in dex + all .so.
- **Evozi web**: apps.evozi.com = static landing (urllib → 403 without UA); ehiapp.com apex (https+www) = 200 with 0-byte body; ehi.sh = domain default page. No web config viewer exists anywhere — decryption is app-only.

## 🎯 NEW PRIMARY LEAD — HTTP Injector Lite 5.3.1 (LATEST Lite) is UNPACKED with the FULL cloud model
- Downloaded via apk.cafe signed-download (no JS gate): `<slug>.apk.cafe` page → `https://apk.cafe/go/?file_id=<id>&b=<base64url>` where `b` = base64(signed filesincloud URL); decode b and curl directly. Worked example: file_id=2357517 → `https://s-02.filesincloud.com/storage/13/704/392/704392/arm64_v8a-armeabi_v7a/com.evozi.injector.lite-5.3.1.apk?s=...&e=<epoch>&lang=en&apk_id=...&premium_speed=0` → 8,075,491 B, PK\x03\x04 verified.
- ⚠️ **Trust the decoded b-param filename, NOT the URL slug**: `https://apk.cafe/download?file_id=2393980/http-injector-lite-...` (LITE slug) actually served the MAIN app 5.4.0 (`HTTP_Injector-5.4.0.apk`, old pre-cloud). Always check the filename inside b.
- Real dex (NOT packed): classes.dex 8,248,004 B + classes2.dex 2,566,784 B (+ audience_network 3.1MB = ads). Zero packer markers (no dexprotector/jiagu/secneo).
- Cloud model found in the dex string pool:
  - Fields: `configSalt`, `configIdentifier`, `configLock`, `configMessage`, `configTimestamp`, `configVersionCode` — exactly the .ehi inner-JSON keys.
  - Classes: `Lcom/evozi/injector/lite/model/EncryptedApi;`, `.../model/HttpObfs;`, `.../model/IAP;`, `.../model/Config;`
  - URLs: `https://www.ehi.tools/`, `https://www.ehiapp.com/`
  - API paths: `/httpinjectorlite/news`, `/httpinjectorlite/timestamp`, `/httpinjectorlite/version`, `/iap/verification`
- Lite versioning is INDEPENDENT of main-app versioning (Lite 5.3.1 ≈ current build; main-app 5.3.1 = 2021). Lite references both ehi.tools and ehiapp.com → same backend family as the main app's blob API.

## NEXT SESSION (scan was mid-flight when session ended)
1. Extract Lite 5.3.1 dex → regex for `CONFIG_AES_KEY`/`OLD_CONFIG_AES_KEY`/`IOS_CONFIG_AES_KEY` + 32/64-hex candidates + `SecretKeySpec`/`Cipher.getInstance` usage.
2. If `EncryptedApi` bytecode is readable (dex is real, likely unobfuscated), the cloud-blob decryption call is IN THERE: key derivation shape (static const vs derived) + schema.
3. Determine whether Lite hits `/httpinjectorlite/*` (Lite-specific) or shares the main `/httpinjector/config` — but the EncryptedApi class reveals the derivation either way.

## Files
- ehi_lite531.apk (8,075,491 B), ehi636_am.apk (54.4MB APKMirror build), ehi636.apk, ehi570.apk, ehi620/611/600.apk, blob_ed242a7S.enc (624 B), test_code_derived.py — all in /opt/work.
