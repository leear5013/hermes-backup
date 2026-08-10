# HTTP Injector cloud-config — Session 16 (2026-08-10) — unpacked window CLOSED

Follow-up to session15-probe.md. Goal: scan the 5.8.1→6.3.5 window APKs for the
server-side `CONFIG_AES_KEY` value. Result: **the window is empty — every real-dex
build predates the cloud feature; every cloud-era build is packed.**

## 1. 6.2.0 / 6.1.1 / 6.0.0 scan results (dex + native libs)

All three downloaded from androidapks dl links (PK\x03\x04 verified), scanned for
`CONFIG_AES_KEY` / `OLD_CONFIG_AES_KEY` / `IOS_CONFIG_AES_KEY` / `configAesKey` /
`configData` / `configSalt` / `Evozi-EHI` / `ehiapp` / `ehi.link` / `httpinjector` /
`EncryptedApi` / `attest_config` / `CLOUD_SAVE` in ALL dex files AND all .so files:

| Version | dex sizes | Cloud strings | Native libs | Verdict |
|---|---|---|---|---|
| 6.2.0 | classes 4.6MB + classes2 6.1MB + adn 3.3MB | ZERO | armeabi-v7a ONLY, DexProtector-packed (`libdexprotector*.so`, `libdpboot.so`, `libol.so`), `libevozi.so` clean | packed, pre-cloud |
| 6.1.1 | classes 4.7MB + classes2 5.8MB | ZERO | same pattern | packed, pre-cloud |
| 6.0.0 | classes 5.3MB + classes2 5.0MB | ZERO | same pattern | packed, pre-cloud |

Combined with prior sessions:
- 5.7.0: REAL 10.6MB dex, ZERO cloud strings (session 14).
- 6.3.6: DexProtector-packed, zero hits in all dex + 30 .so (session 14).
- 6.4.1 / 6.5.0: DexHelper-packed; only `libdatajar.so` string pool has the
  `/httpinjector/*` paths + constants NAMES (sessions 8/9).

**Conclusion: static APK scanning for the `CONFIG_AES_KEY` VALUE is exhausted.**
Every build with readable dex (≤6.2, and 5.7.0) predates the cloud blob API; every
cloud-era build (≥6.3.2) is DexProtector/DexHelper-packed with the key in encrypted
bytecode. Remaining routes: Frida hook of `SecretKeySpec`/`Cipher.init` on a device,
rooted memory dump of the decrypted dex, MITM of a real in-app cloud import, or an
unpacked/repacked 6.3.2–6.3.6 build (none found on archive.org/androidapks/apk.cafe).

## 2. APKMirror changelog pins the feature introduction: v6.3.2

From the APKMirror 6.3.6 release page (web search snippet, 2026-08-10):
- **v6.3.2 [Added] "New cloud config import"** (2024-04) — the share-key/AES-blob
  feature landed in 6.3.2. 6.3.2–6.3.6 are all DexProtector-packed → the feature was
  born packed; no unpacked first-version exists on the usual mirrors.

## 3. apk.cafe mirror flow (verified working, no JS gate)

- App page: `https://<slug>.apk.cafe/` → version list with per-version
  `https://apk.cafe/download?file_id=<id>/<slug>` links.
- Download page is HTML (not the APK): it embeds
  `href="https://apk.cafe/go/?file_id=<id>&b=<base64url>"` where
  `b = base64.b64encode(signed_url)` and the signed URL is
  `https://s-02.filesincloud.com/storage/<n>/<n>/<n>/<n>/<abis>/<pkg>-<ver>.apk?s=<sig>&e=<epoch>&lang=en&apk_id=<id>&premium_speed=0`.
  Decode: `base64.b64decode(urllib.parse.unquote(b))` → curl that URL directly.
- HTTP Injector Lite dead lead: newest Lite on apk.cafe = **5.3.1** (pre-cloud) —
  Lite does not share the cloud backend; don't hunt it for the key.

## 4. Blob brute-force refresher (already in session-13 note)

Blob is per-request encrypted (random IV, varying size). Validated-hit detector must
use printable-ratio >0.9 AND strict `json.loads` or `.ehi` magic `\x00\x03ehi` — a
bare `{`/`}` check fires 93 false positives on random binary (session 15).

## State for next session

- `/opt/work/` holds: turkcell.ehi (+ turkcell_FINAL.json — DECRYPTED, the deliverable),
  ehi_decrypt.py (working full .ehi pipeline), ehi570_dex.bin, ehi636.apk, ehi620.apk,
  ehi611.apk, ehi600.apk, ehi531.apk, old_ehi.apk, blob_ed242a7S.enc (fresh fetch).
- The .ehi LOCAL-file decrypt problem is SOLVED end-to-end (see SKILL.md session-12
  note + scripts/ehi_full_decrypt.py). Only the CLOUD blob needs the server key.
