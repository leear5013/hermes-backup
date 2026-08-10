# HTTP Injector Lite 5.3.1 — string-deobfuscation chain FULLY DUMPED (session 19B, 2026-08-10)

## Context
Lite 5.3.1 (apk.cafe filesincloud download) is UNPACKED: real 8.2MB classes.dex + 2.5MB classes2.dex,
ZERO packer markers. Cloud model present in string pool:
- `com.evozi.injector.lite.model.EncryptedApi` — Gson fields `_encrypt`, `_decrypt`, `_encryptIV`,
  `_decryptIV`, `_encryptSaltSet`, `_decryptSaltSet` (snake_case = Gson serialized names)
- Models: `HttpObfs`, `IAP`, `News`, `Timestamp`, `Version`, `Profile`, `Server`, `Config`
- URLs: **`https://www.ehi.tools/`** (NEW host — not seen in main-app .so pools!) +
  `https://www.ehiapp.com/`
- API paths: `/httpinjectorlite/news`, `/httpinjectorlite/timestamp`, `/httpinjectorlite/version`
- Helpers: `AesCbcWithIntegrity` (crypto) + `Unseal` (reflection utility)

## The obfuscation scheme (all string constants encrypted)
Decode pipeline, three classes in `com.google.android.gms.internal`:

`ﻢ.ﾠ⁬͏(J)String` (thin wrapper) → `sget` the 7-element `[Ljava/lang/String;` built in
`ﻢ.<clinit>` (each element = a GIANT CJK/emoji string = encrypted string blob) →
`ｎ.ﾠ⁮͏(J, [String])` (dissector) → uses `b0.ﾠ⁬͏(J)` + `b0.ﾠ⁫⁫(J)` (mixers) → plaintext String.

Call sites pass NEGATIVE long constants (e.g. -78612227362228, -78702421675444, -78719601544628,
-78801205923252, -77920737627572, -77937917496756, -77985162137012, -78066766515636, ...).

## ｎ.ﾠ⁮͏(J [Ljava/lang/String;)Ljava/lang/String;  (the dissector — bytecode-verified)
```
low  = (int) arg                # 4294967295 & arg
v0   = b0.ﾠ⁫⁫(low)             # 64-bit mixer on the LOW word
v0   = b0.ﾠ⁬͏(v0)             # 16-bit lane transform
len  = (v0 >>> 32) & 0xFFFF     # output length
v0   = b0.ﾠ⁬͏(v0)             # re-mix
v7   = (v0 >>> 16) & 0xFFFF0000
base = ((arg >>> 32) ^ len ^ v7) & 0xFFFFFFFF   # long-to-int
for i in range(len):
    idx = base + i + 1
    v0  = ｎ.ﾠ⁬͏(idx, array, v0)   # per-index extractor (re-mixes each call)
    out[i] = chr((v0 >>> 32) & 0xFFFF)
return ''.join(out)
```

## ｎ.ﾠ⁬͏(I [Ljava/lang/String; J)J  (per-index extractor)
```
v3 = b0.ﾠ⁬͏(long_arg)           # re-mix the long each call
seg = array[idx // 8191]        # blobs split into 8191-char segments
c   = ord(seg[idx % 8191])
return (c << 32) ^ v3
```

## b0.ﾠ⁫⁫(J)J  (64-bit mixer — splitmix64-style, constants from bytecode)
```
x ^= x >>> 33
x *= 0x62A9D9ED799705F5        # 7109453100751455733
x ^= x >>> 28
x *= 0xCB24D0A5C88C35B3        # -3808689974395783757 (Java signed → two's complement)
x ^= x >>> 32
return x & 0xFFFFFFFFFFFFFFFF
```

## b0.ﾠ⁬͏(J)J  (16-bit lane transform, packed into 64-bit)
```
lo = (short)(arg & 0xFFFF); hi = (short)((arg >> 16) & 0xFFFF)
s1 = (short)(lo + hi);      s1 = rotl16(s1, 9);  s1 = (short)(s1 + lo)
s2 = (short)(hi ^ lo)
x  = (short)(rotl16(lo, 13) ^ s2 ^ (s2 << 5))
s3 = (short)rotl16(s2, 10)
return (s1 << 32) | (s3 << 16) | (x & 0xFFFF)
```
`b0.ﾠ⁮͏(S I)S` = rotate-left on 16-bit lanes: `((s << n) | (s >>> (32 - n)))`.

## AesCbcWithIntegrity = Tozny java-aes-crypto (IDENTIFIED — standard library, no custom crypto)
- `ﾠ͏⁫(String password, byte[] salt, int iterations)` = `PBEKeySpec(password.toCharArray(), salt,
  iterations, ...)` + `SecretKeyFactory("PBKDF2WithHmacSHA1")` → `getEncoded()` → split:
  `[0:16]` = AES key, `[16:48]` = HMAC key (both wrapped in SecretKeySpec with decoded "AES" /
  "HmacSHA256").
- `ﾠ⁬⁪(data, SecretKey)` = `Mac.getInstance(decoded "HmacSHA256")` over data.
- `ﾠ⁫⁫(blob, keys)` = constant-time HMAC compare (`ﾠ⁬͏([B [B)Z` = xor-or accumulator), then
  AES/CBC/PKCS5Padding decrypt with IV from blob.
- Blob layout (Tozny standard): `IV(16) || ciphertext || HMAC(32)`.
- `ﾠ⁬(String b64, keyObj, String algo)` = Base64.decode (flag 2) → encrypt with random IV (16B from
  `ﾠﾠ(I)[B`) → `IV || ct || HMAC(IV||ct)`.
- `ﾠ⁭(String b64, keyObj, String algo)` = the DECRYPT entry point (used by the cloud path).

## NEXT-STEP STATE (session ended here — Python port IN PROGRESS)
1. Implement the dissector chain in Python (constants + bytecode above are complete).
2. Extract the 7 blob strings from `ﻢ.<clinit>` (each is a literal in the androguard dump).
3. Decode the negative-long constants at `AesCbcWithIntegrity.<clinit>` + call sites
   (`ﾠ͏⁪`, `ﾠ͏⁫`, `ﾠ⁪͏`, `ﾠ⁬`, `ﾠ⁫⁫`, `ﾠ⁭`, `ﾠ⁬⁪`) — these decode to "AES", "HmacSHA256",
   "PBKDF2WithHmacSHA1", the PBE PASSWORD, cipher strings, error strings.
4. The PBE password + salt → PBKDF2 → AES+HMAC keys → Tozny-decrypt the cloud blob / EncryptedApi
   JSON (`_decrypt`+`_decryptIV`+`_decryptSaltSet`).
5. Whether Lite's password == main app's `CONFIG_AES_KEY` is UNKNOWN — test the decrypted
   password against the main-app blob (`POST https://www.ehiapp.com/httpinjector/config`).

## Reusable technique: cracking a dex string-constant obfuscator with androguard
1. Find the wrapper class: `<clinit>` fills a `[Ljava/lang/String;` table + a `(J)String` method.
2. Dump the delegator (`(J [Ljava/lang/String;)String`) — usually small index/arithmetic over the long.
3. Dump its helper classes (mixers) — tiny pure functions, trivially portable to Python.
4. Only inputs per string = the negative long constant; the String[] table is shared/clinit-built.
Port order: mixers → per-index extractor → dissector → wrapper → collect all call-site constants.
