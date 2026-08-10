# HTTP Injector cloud-key hunt — session 17 (2026-08-10)

Goal: recover the server-side `CONFIG_AES_KEY` that decrypts the cloud-config
blob from `POST https://www.ehiapp.com/httpinjector/config`. Continued from
session 16 ("static key hunt exhausted"). Outcome: **still blocked**, but the
APKMirror download chain was cracked and the packer timeline is now fully pinned.

## New this session

### APKMirror chain cracked (cookie-bound, key rotates per hop)
Previously recorded as "JS-gated / broken" — actually walkable with a cookie jar:
1. Variant page with `curl -c cookies` → embeds `/download/?key=<key1>`.
2. GET `/download/?key=<key1>` with `-b/-c cookies` + browser Referer → variant
   page again, but with a **rotated** `<key2>` in the download anchor.
3. GET `/download/?key=<key2>` → 433KB page with
   `id="download-link" href="/wp-content/themes/APKMirror/download.php?id=<id>&key=<key3>"`.
4. GET download.php (same jar) → APK (final hop not verified — session cut).
Keys are per-session; re-extract from each hop's response, never reuse stale keys.

### Packer timeline pinned (all downloaded builds scanned)
| Version | Source | dex | Verdict |
|---|---|---|---|
| 6.3.6 (54.9MB) | androidapks dl | 1.7MB stub | **DexProtector-packed** (libdexprotector*.so/libdpboot.so/libol.so, NO libdatajar.so); zero cloud-key hits in dex + 30 .so |
| 5.7.0 (18.3MB) | androidapks dl | 10.6MB REAL (classes.dex 6.36MB + classes2.dex 0.84MB + audience_network.dex 3.4MB) | NO cloud strings at all → cloud feature absent in 5.7.0 |
| 6.2.0 (34.0MB) | androidapks dl | 14.1MB | **DexProtector-packed** (armeabi-v7a only); no cloud strings |
| 6.1.1 (33.3MB) | androidapks dl | 13.8MB | **DexProtector-packed**; no cloud strings |
| 6.0.0 (28.5MB) | androidapks dl | 13.5MB | **DexProtector-packed**; no cloud strings |

APKMirror changelog (from the 6.3.6 release page): **v6.3.2 [Added] "New cloud
config import"** — cloud feature born packed. Combined with sessions 14–16:
every readable-dex build (≤6.2 + 5.7.0) predates the feature; every cloud-era
build (6.3.2+) is packed. **The unpacked-window lead is CLOSED for good.**

### Dead leads confirmed
- **HTTP Injector Lite** (com.evozi.injector.lite): apk.cafe newest = 5.3.1 —
  pre-cloud, no shared backend. Don't chase.
- GitHub code search (Bearer token): `"IOS_CONFIG_AES_KEY"`, `"Evozi-EHI"`,
  `"httpinjector/config"`, `"com.evozi.injector" "EncryptedApi"` → 0 public
  hits (the `"CONFIG_AES_KEY" "CBC"` 147 hits are unrelated AES C code).
- 32-char alphanumeric strings adjacent to crypto words in string pools
  (`basxIWwUdkqjCj33WkHPX1XLcRlnz9UL` next to `baseUrl`) are random identifiers
  (pools sort alphabetically) — not keys.

### Blob behavior (re-confirmed)
Re-fetched blob for `ed242a7S`: 624 B this time (was 592 B), new random IV →
per-request encryption, stable key. `fetch_blob.py` in /opt/work (urllib,
X-Platform: android, body {"key": code}).

## Remaining routes (unchanged, from session 16)
Frida hook of `SecretKeySpec`/`Cipher.init` on a device, rooted memory dump,
MITM of a real in-app import, or an unpacked 6.3.2–6.3.6 build (none found).

## Artifacts in /opt/work (VPS scratch, may be wiped)
ehi636.apk, ehi570.apk, ehi620.apk, ehi611.apk, ehi600.apk, blob_ed242a7S.enc,
test_basx_key.py, cloud_brute.py, fetch_blob.py. Working .ehi decryptor:
ehi_decrypt.py (full pipeline incl. Java-char configMessage XOR) — see SKILL.md.
