# HTTP Injector cloud-blob hunt — Session 19G probe (2026-08-10)

Continuation of the Lite-app deobfuscation work (sessions 19A–19F). Goal: recover the
password/key that decrypts the cloud-config blob from `POST https://www.ehiapp.com/httpinjector/config`.

## What happened

1. Re-ran the pending candidate test from session 19F → **66 candidates, 0 hits** (`test_c3843.py`):
   - `UNIVERSAL_KEY` (Lite `utils/Constant.java`, 256-char base64 → 192 decoded bytes) as raw,
     b64-decoded, sha256/sha1/md5, first16/first32/last16 slices
   - `SIGNATURE` (`ARsgBGVYjoAFCF0NRv89Og0ezAkFw1rpOg0ZfA==`, 32 decoded bytes) raw + hashes
   - `XOR_KEY` (`EVOZI`) raw + hashes
   - share code `ed242a7S` ± case, hosts (`ehiapp.com`, `ehi.tools`, `www.*`), `httpinjector`,
     `httpinjectorlite`, `config` — each as raw bytes AND sha256/sha1/md5
   - All tried as AES-CBC with the blob's own IV (blob[:16]) → **no valid PKCS7 unpad anywhere**.
   - Conclusion: **cloud-blob key is NOT any Lite static string, NOT f(share-code), NOT the
     Settings.Secure-derived local-prefs password.** The Lite app shares Evozi's backend but its
     cloud decrypt entry was never found (see Next steps).

2. **jadx decompile of `ehi_lite531.apk` → `C3843` class** (`com.google.android.gms.internal.C3843`,
   renamed from `ﾠﾠ͏`):
   ```java
   m13503(String str) → SecretKeySpec(SHA-256(str.getBytes("UTF-8")), "AES")
   m13504(SecretKeySpec, iv, data) → Cipher AES/CBC/PKCS7Padding, decrypt (mode 2)
   m13505(SecretKeySpec, iv, data) → same, encrypt (mode 1)
   ```
   Simple scheme: **key = SHA-256(any string), AES/CBC/PKCS7**. Found via jadx; callers found
   via androguard smali (grep for `Lcom/google/android/gms/internal/ﾠﾠ͏;->`).

3. **`הּ` class = the .ehi FILE-import path, NOT the cloud path** (decompiled, 688 lines):
   - `<init>(Context, int)`: derives a key from `PackageInfo.signatures` (MessageDigest + Base64)
     + `context.getString(...)` build strings + substring + `replaceAll` — app-signature-derived.
   - `ﾠﾠ(DataInputStream)`: reads the .ehi container (readUTF magic, readInt×2, readUTF, readLong,
     readInt, readLong, then payload with **Adler32 checksum verification**).
   - `ﾠ⁪͏(Context, Config)`: decrypts a LOCKED config — password = `ﾠ⁬͏(Config)` (a static method
     returning String derived from the Config object itself; matches the ehi.go cross-ref: the
     config JSON's OWN `configAesKey` feeds the lock layer), via
     `AesCbcWithIntegrity.ﾠﾠ͏(password, keySpec)`, then re-encrypts with
     `C3843.ﾠ⁮͏(SHA-256(appSig), ť.ﾠ⁬͏ [B, data)` where **`ť.ﾠ⁬͏` is a static IV byte-array field —
     untraced yet**.

4. **Retrofit annotations: 8+ androguard API variants all dead** on the `ᵤ` interface:
   - `EncodedMethod` has no `get_annotations` / `get_class_def`
   - `DEX` has no `get_classdefs` (use `get_classes()`); `get_classes_def_item()` → `ClassHDefItem`
     with only `get_method(i)`/`get_obj`/`get_raw`; `get_length()` raises `KeyError` on this dex
   - `ClassDataItem.get_methods()` → `EncodedMethod` (no annotations either)
   - jadx also loses the class (renamed/vanished)
   - **Workaround: parse `method_annotation_items` from raw dex, or trace callers.**

5. **jadx coverage rule confirmed**: for ehi_lite531.apk, `grep -rl "ehi.tools\|ehiapp\|BaseApplication\|lI"` over `jadx_out/sources` → **0 hits**. Obfuscated `com.google.android.gms.internal.*` classes vanish or become `C1407.java`-style renames. jadx is only useful for readable packages: `com.evozi.injector.lite.utils.Constant`, `model/*` (Profile/Config/EncryptedApi/Server/IAP), `event/*`.

6. **Profile.java = the cloud Profile JSON field list** (validation oracle — plaintext must
   `json.loads()` AND contain ≥2 of these):
   configExpiryTimestamp, configHwid, configIdentifier, configMessage, configSalt, configTimestamp,
   configVersionCode, customDns1, customDns2, customRoutes, dnsType, excludedRoutes, host,
   isCompression, isConfigLock, isDNSProxy, isDefaultRoute, isPublicKey, isUpstreamProxy,
   localPort, lockModes, lockModesHash, overwriteServerData, overwriteServerProxyPort,
   overwriteServerType, password, payload, port, publicKey, remoteProxy, remoteProxyAuth,
   remoteProxyPassword, remoteProxyUsername, shadowsocksEncryptionMethod, shadowsocksHost,
   shadowsocksPassword, shadowsocksPort, sniHostname, startSsh, tunnelType, upstreamProxy, user.

7. **`EncryptedApi` model = `{data: String, status: int}` only** — the Retrofit response type.
   API interface `ᵤ` has 4 methods (all return `retrofit2.Call`):
   `ﾠ⁪͏(String,String,int)`, `ﾠ⁫⁫(Str,Str,Str)`, `ﾠ⁬͏(Str,Str,int)`, `ﾠ⁮͏(Str,Str,Str,Str)`.
   Callers seen: `ۥۢ۫ۤ` (a Fragment, mostly ads/billing) and `ィ.ﾠ⁪` (billing purchase flow).
   `x6.ﾠ⁮͏(String)` = hashing helper used in shadowsocks `ss://` URI building.

## Next steps (state at session end)

- **Find who consumes the `EncryptedApi` Retrofit response** and how `data` is decrypted. The
  Lite cloud decrypt entry is STILL unfound — `AesCbcWithIntegrity.ﾠ͏⁫` (PBE entry) callers were
  only: public API, the encrypted-SharedPreferences wrapper (`helper/ﾠ⁬͏`, device-unique password
  from `Settings.Secure`), and `helper/ﾠ⁬͏.ﾠ⁭(Context, int)` whose password source is untraced.
- Trace `ť.ﾠ⁬͏` static `[B` field (IV for the file-import decrypt) — may be a shared constant.
- Try `API_VERSIONINFO = /apps/injector/update/?type=android` on `ehi.tools`/`ehiapp.com`.
- Remaining fallbacks: Frida hook, rooted memory dump, MITM of a real in-app import.

## Working artifacts this session

- `/opt/work/test_c3843.py` — 66-candidate key test (raw/hash/base64 variants × blob IV)
- `/opt/work/Deobf2.java` — the PROVEN deobfuscator (sign-extended 16-bit mixer fix;
  `((long)v<<32)|((long)r2<<16)|((long)t)` — the final OR term must sign-extend `t` too;
  this was the last semantics bug, after which ALL 14 constants decoded correctly)
- `/opt/work/ehi_lite531.apk`, `jadx_out/` (partial coverage), `/opt/work/blob_ed242a7S.enc`
