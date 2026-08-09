# Hunting closed-source VPN APKs (NetMod etc.) for ground-truth keys

Goal: pull the actual APK of a closed-source tunnel app (e.g. NetMod `com.netmod.syna`)
so we can decompile it and extract the current config-encryption key. Community
decryptors often ship STALE keys (see nm-vmess-format.md — `_netsyna_netmod_` failed
on a real 4.x sample), so the APK is the only ground truth.

## What WORKS from the VPS (verified 2026-08-08)

0. **APKMirror download chain (VERIFIED 2026-08-09, HTTP Injector 6.5.0):**
   - Index: `https://www.apkmirror.com/apk/evozi/http-injector/` → links like
     `/apk/evozi/http-injector/http-injector-ssh-v2ray-vpn-6-5-0-release`.
   - Release page: grep `href="[^"]*-android-apk-download/"` (universal variant
     has NO `-2-` in the slug; `...-6-5-0-2-android-apk-download/` is the
     armeabi-only variant). The `download` link on this page is ONLY social
     share buttons — do NOT regex `href="[^"]*download[^"]*"` blindly, the
     FIRST hit is a twitter/telegram share URL.
   - Variant page → keyed URL: `grep -oE 'href="[^"]*/download/\?key=[0-9a-f]{40}"'`
     → `https://www.apkmirror.com/apk/.../download/?key=<40-hex>` → **the APK
     bytes, content-type application/vnd.android.package-archive**. The old
     `download.php?id=...&key=...` pattern is gone (2026).
   - Beware: fetching the variant page's own URL back (self-referencing href)
     yields the HTML shell (456KB) — check content-type/length before trusting.

1. **Find the official Telegram channel with ddgs** (public preview is scrapeable):
   `ddgs.text('netmod vpn telegram channel official t.me')` → `t.me/netmod_vpn_channel`.
2. **Read channel preview** `curl -sL 'https://t.me/s/<channel>'` — HTML contains post
   texts + document titles (e.g. `Version 4.2.0.635 - Universal.apk`) + links to posts.
   NOT included: direct file download URLs. Documents on preview pages expose title +
   size only; `?single` post pages expose at most an `og:image` (photos only).
3. **APK mirrors**: `apkcombo.com` works (HTTP 200, no Cloudflare wall from this VPS).
   Other mirrors (apkpure.com, apkpure.net, pgyer.com, sourceforge.net HTML **and**
   RSS/`best_release.json` endpoints) are Cloudflare-challenged/403 from this IP.
4. **apkcombo signed-download trick** (the key move):
   - App page: `https://apkcombo.com/<slug>/com.netmod.syna/` → version list links:
     `.../download/phone-4.2.0-apk` (latest), `.../download/apk`, `.../old-versions/`.
   - Fetch the version page, then grep for links containing `d?u=`:
     `grep -oE 'https://apkcombo.com/d\?u=[^"&]+'` — each `u` param is **base64**.
   - Decode: `base64.b64decode(u + "="*(-len(u)%4))` → the REAL file URL, e.g.
     `https://download.pureapk.com/b/XAPK/<base64-ish path>?as2=<sig>&k=<key>...`
     (signed, time-limited; must be used promptly).
   - Download: `curl -L '<decoded-url>' -o netmod.apk` then verify magic bytes
     (`PK\x03\x04` — APK/XAPK are zips). `file` may be absent on slim hosts; use
     `head -c 4 | od -An -c`.
5. **If Telegram mirror needed instead**: the channel attaches APKs as documents, but
   preview pages won't hand you the file. Options: have the user forward the APK to
   the decrypt bot (bot API gives you the file_id), or use a MTProto client.

## Dead ends from this VPS (do not burn time retrying)
- netmodvpnclient.com: WordPress, download buttons are JS-driven `href="#"` — no APK
  URL in HTML. Site copy confirms "Private Configuration Files" = the encrypted
  `nm-vmess` feature.
- sourceforge.net/projects/netmodhttp: real project but Cloudflare "Just a moment..."
  challenge on HTML, RSS, and JSON endpoints.
- GitHub code search for `nm-vmess` schema: auth-gated (401); grep.app: Vercel block.

## Verified download + XAPK structure (completed 2026-08-08)
- `curl -L '<decoded pureapk URL>' -o /tmp/netmod_4.2.0.xapk` → HTTP 200,
  33,050,566 bytes, `content-type: application/xapk-package-archive`, magic `PK\x03\x04`. ✓
- XAPK is a zip of: the real app APK + split configs + `manifest.json`:
  `com.netmod.syna.apk` (16.7 MB — THE one with classes.dex),
  `config.armeabi_v7a.apk` (15.6 MB — native libs, skippable for key hunting),
  `config.<lang>.apk`, `icon.png`, `manifest.json` (versionCode 635 → NetMod 4.2.0).
- Extract with **python zipfile** (`zipfile.ZipFile(xapk).extract('com.netmod.syna.apk', ...)`)
  — `unzip`/`file` binaries are NOT installed on this VPS.

## Decompiling WITHOUT java (this VPS has no java/jadx/apktool — and no `strings` binary either!)
The APK is a zip; pull `classes*.dex` out with python zipfile, then hunt the key in
dex bytes directly — no jadx needed for a hardcoded string. **Re-runnable scanner:
`scripts/scan-dex-strings.py`** (takes an .apk or .xapk, extracts all dex files, regex-filters
printable runs, dedupes). Verify it on the extracted APK:
`/opt/venv/bin/python scripts/scan-dex-strings.py /tmp/netmod_xapk/com.netmod.syna.apk`
- Python approach that WORKED (bash `strings` is NOT installed — don't rely on it):
  `re.findall(rb'[ -~]{4,}', dex_bytes)` then filter — 16-byte keys look like
  `_netsyna_netmod_` (the OLD one) or 16 chars of mixed case/digits; candidates sit
  near AES-mode/`decrypt` string references.
- **NetMod 4.2.0 scan results (verified):** `nm-vmess://` + the full scheme-family regex
  in classes2.dex; `AESSettingsCipherMode`; `Lnetmodcore/Netmodcore;` + `Lgo/netmodcore/gojni/R;`
  (Go native bridge — key lives in `.so`, NOT dex); SQLCipher classes for the local DB.
- Native-lib option (NEXT STEP, not yet done): the key may live in a `.so` inside
  `config.armeabi_v7a.apk` (15.6 MB, contains lib/ for armv7). Extract that split APK and
  scan the `.so` bytes the same way — Go string data survives in native binaries.
- Once a candidate key is found: re-test on the user's real sample (272 bytes =
  17×16 AES blocks, first byte 0xAB) with AES-128-ECB/CBC, and if CBC try the first
  16 bytes as IV with the rest as ciphertext.
