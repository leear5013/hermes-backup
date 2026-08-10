# HTTP Injector Lite 5.3.1 — Evozi string-deobfuscation chain CRACKED (session 19D, 2026-08-10)

## Context
HTTP Injector Lite 5.3.1 (`ehi_lite531.apk` from apk.cafe, UNPACKED — real 8.2MB classes.dex) contains
the full cloud model (`EncryptedApi`, `AesCbcWithIntegrity`, Tozny java-aes-crypto). All its strings
are obfuscated behind a long-constant + string-array deobfuscator. This session PROVED the chain by
decoding the crypto-algorithm constants. This is the key to the cloud blob (`CONFIG_AES_KEY`).

## The chain (classes)
- `com/google/android/gms/internal/ﻢ` — `<clinit>` builds a 7-element `[Ljava/lang/String;` table of
  giant CJK/emoji blobs (each ≤8191 chars), then method `ﾠ⁬͏(J)Ljava/lang/String;` = thin wrapper:
  `sget` table → `invoke-static` `ｎ.ﾠ⁮͏(J [Ljava/lang/String;)Ljava/lang/String;`.
- `com/google/android/gms/internal/ｎ` — the dissector:
  - `ﾠ⁮͏(J [String])String`: `v0 = j & 0xFFFFFFFF` → `v0 = b0.ﾠ⁫⁫(v0)` → `v0 = b0.ﾠ⁬͏(v0)`;
    `v3 = (v0>>>32) & 0xFFFF`; `v0 = b0.ﾠ⁬͏(v0)`; `v7 = (v0>>>16) & 0xFFFF0000`;
    `v11 = (j>>>32) ^ v3 ^ v7` → `idx = (int)v11`; `r = ﾠ⁬͏(idx, arr, v0)`;
    `n = (r>>>32) & 0xFFFF` = length; loop `i`: `r = ﾠ⁬͏(idx+i+1, arr, r)`,
    char = `(r>>>32) & 0xFFFF`.
  - `ﾠ⁬͏(I [String] J)J`: `x = b0.ﾠ⁬͏(j)` — **ONLY mix16, NO mix64** (this was the extra-mix bug);
    `seg = idx/8191; pos = idx%8191` (from the CHAR index, not the mixer);
    `return (((long)arr[seg].charAt(pos)) << 32) ^ x`.
- `com/google/android/gms/internal/b0` — the mixers:
  - `ﾠ⁫⁫(J)J` = splitmix64: `x ^= x>>>33; x *= 0x62A9D9ED799705F5; x ^= x>>>28; x *= 0xCB24D0A5C88C35B3; x >>>= 32`.
  - `ﾠ⁬͏(J)J` = 16-bit lane transform: `lo_s=(short)(j&0xFFFF); hi_s=(short)((j>>>16)&0xFFFF);
    v=(short)(lo_s+hi_s); v=rot(v,9); v=(short)(v+lo_s); x1=(short)(hi_s^lo_s);
    t=(short)((short)(rot(lo_s,13)^x1) ^ (x1<<5)); r2=rot(x1,10);
    return ((long)v<<32)|((long)r2<<16)|((long)t)`.
  - `ﾠ⁮͏(S I)S` = rot: `int v32=v; int a=v32<<n; int b=v32>>> (32-n); return (short)(a|b)`.

## The 5 Java-semantics traps that killed 4 Python ports
1. `ushr-long`/`ushr-int` are LOGICAL shifts. Python `>>` on a signed int is arithmetic —
   do `(x & MASK) >> n` first.
2. `int-to-short` sign-extends: truncate to 16 bits then subtract 0x10000 if ≥ 0x8000.
3. `int-to-long` on a short sign-extends to 64 bits — negative shorts pollute bits 48-63 with
   0xFFFF. Final `out = ((long)v<<32) | ((long)r2<<16) | ((long)t)` — ALL THREE terms sign-extended.
   Using `(t & 0xFFFFL)` silently zeroes the high bits → wrong idx by ~1.3e9.
4. The rotl helper rotates the SIGN-EXTENDED 32-bit int (`v32 >>> (32-n)`), not a clean 16-bit rotate.
5. `shl-int/lit8 v4, 5` shifts the sign-extended 32-bit int before the int-to-short truncation.

## Working recipe (proven)
- Install Java: `apt-get install -y default-jdk` (Debian 13; `default-jre-headless` has no javac).
- Extract the 7 blobs in aput-object order: `scripts/extract_lite_enc_strings.py`
  (Lite 5.3.1 string-pool indices 59939, 59935, 59937, 59925, 59929, 59924, 59936; lens 8191×6+2355)
  → writes `enc_strings.txt` (one per line, UTF-8).
- `scripts/Deobf.java`: `javac Deobf.java && java Deobf`.
- PROVEN OUTPUT (algorithm constants):
  `AES/CBC/PKCS5Padding`, `AES`, `PBKDF2WithHmacSHA1`, `HmacSHA256`, `UTF-8`.

## Decoded constants so far (crypto algorithms)
- -78612227362228 → AES/CBC/PKCS5Padding
- -78702421675444 → AES
- -78719601544628 → PBKDF2WithHmacSHA1
- -78801205923252 → HmacSHA256
- -77920737627572 → AES
- -77937917496756 → HmacSHA256
- -77985162137012 → PBKDF2WithHmacSHA1
- -78066766515636 → AES
- -78083946384820 → HmacSHA256
- -78247155142068 → UTF-8

## NEXT (session 19E)
- Decode remaining constants: `ﾠ⁬͏` clinit set `-78156960828852, -78564982721972` + the
  `AesCbcWithIntegrity.<clinit>` four (-78612227362228 was #1 above; full list in Deobf.java consts
  array) — these include the PBE **password**.
- Then: Tozny java-aes-crypto decode of the cloud blob — `PBKDF2WithHmacSHA1(password, salt, 384)`
  → first 16B = AES key, next 32B = HMAC key; blob = `IV || AES-CBC-PKCS5(ct) || HMAC-SHA256(iv||ct)`;
  verify against blob from `POST https://www.ehiapp.com/httpinjector/config` (X-Platform: android).
