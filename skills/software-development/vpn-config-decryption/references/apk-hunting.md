# Hunting closed-source VPN APKs (NetMod etc.) for ground-truth keys

Goal: pull the actual APK of a closed-source tunnel app (e.g. NetMod `com.netmod.syna`)
so we can decompile it and extract the current config-encryption key. Community
decryptors often ship STALE keys (see nm-vmess-format.md — `_netsyna_netmod_` failed
on a real 4.x sample), so the APK is the only ground truth.

## What WORKS from the VPS (verified 2026-08-08)

0. **APKMirror download chain (BROKEN 2026-08-09 — JS-gated; use apkcombo §4 instead):**
   Historically: index → release page → variant page → `/download/?key=<40-hex>`
   → APK bytes. NOW fetching the keyed URL returns `text/html` (457KB) with
 `?redirected=t` — the download is gated behind JS from this VPS. Kept as
 reference only.
 **REFINEMENT (2026-08-10, HTTP Injector 6.3.6): the chain is NOT dead — it
 advances if you use a cookie jar and RE-EXTRACT the key at every hop.**
 Verified sequence: (1) variant page with `-c cookies` → page embeds
 `/download/?key=<key1>`; (2) GET that with `-b/-c cookies` + Referer → returns
 the variant page again but with a **FRESH rotated key** `<key2>`; (3) GET
 `/download/?key=<key2>` same jar → 433KB page containing
 `id="download-link" href="/wp-content/themes/APKMirror/download.php?id=<id>&key=<key3>"`;
 (4) GET that download.php (same jar) → should be the APK (final hop was
 in-flight when the session ended — VERIFY bytes `PK\x03\x04` before trusting).
 **Key pitfall: keys rotate per session — a key scraped from one page 404s/
 shells when reused; you MUST re-extract `<key2>`/`<key3>` from the response
 of the previous hop in the SAME cookie-bound session.** So a stale key
 (e.g. from a saved HTML dump) is useless — the chain must be walked live.
   - Index: `https://www.apkmirror.com/apk/evozi/http-injector/` → links like
     `/apk/evozi/http-injector/http-injector-ssh-v2ray-vpn-6-5-0-release`.
   - Release page: grep for `-android-apk-download/` hrefs (universal variant has
     NO `-2-` in the slug; `...-6-5-0-2-android-apk-download/` is the armeabi-only
     variant). The `download` link on this page is ONLY social share buttons —
     do NOT regex `href=...download...` blindly, the FIRST hit is a twitter share URL.
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
   - **Newer apkcombo variant that ALSO WORKS (2026-08-09, HTTP Injector 6.5.0):**
     the `/download/apk` page embeds `<a href="/r2?u=<url>">` links where `u` is
     DOUBLE percent-encoded (not base64). `urllib.parse.unquote` twice → real R2
     storage URL (`apks.<hash>.r2.cloudflarestorage.com/...`). GET
     `https://apkcombo.com/r2?u=<encoded>` with a browser Referer → 200,
     `content-type: application/xapk-package-archive`, real bytes. `.apks` = zip of
     `com.<pkg>.apk` (base) + `config.<arch>/<lang>.apk` splits + manifest.json —
     extract base with python zipfile.
   - **PACKED-APK PITFALL + THE FIX (HTTP Injector 6.5.0, 2026-08-09):** base
     `classes.dex` (22KB) is a DexHelper/ACFNAME packer stub — real code encrypted,
     dex strings-scan is useless. `assets/audience_network/*.dex` = Meta ads SDK (noise
     only). `resources.arsc` strings-scan works (found `https://http-injector.firebaseio.com`
     + `httpinjector.com` still embedded). **BUT the whole app string table (class
     names + API paths + UA) survives as PLAINTEXT in the native split libs** — extract
     `config.arm64_v8a.apk` (or armeabi variant) from the .apks and regex-scan
     `lib/arm64-v8a/libdatajar.so` (~20MB, the packed-dex carrier; contains NO dex
     magic itself) and `libdexjniehi.so` (ehi-cloud JNI bridge). This is what found
     the cloud API paths `/httpinjector/{config,import_config,export_config,backup,
     login,servers,attest_config}` + `/iap/verification` + `User-Agent: Evozi-EHI/1.4.1`
     that the base-APK dex scan missed entirely. No unpacking needed.
   - apkcombo old-versions page only lists the last ~3 versions (HTTP Injector:
     6.4.0/6.4.1/6.5.0 only); the `/versions/` page has the same 3 — no older
     unpacked build. 6.4.1 DOES download via the identical r2 chain
     (`/download/phone-6.4.1-apk` → `/r2?u=` → 68.7 MB `application/xapk-package-archive`).
     **Disk-full pitfall (bit us 2026-08-09): extracting a 68 MB .apks into
     `/data/workspace` died with `OSError: [Errno 28] No space left on device` —
     /data has a 500 MB budget; extract large bundles into `/opt` or `/tmp` (1.8 TB
     overlay) and copy only small artifacts (dex/so string dumps) back.**
     APKMirror keyed `/download/?key=` URL now returns an HTML shell redirect
     (`?redirected=t`) from this VPS; Softpedia 403s.
     6. **Other mirror that WORKS (2026-08-10, HTTP Injector 6.3.6 + 5.7.0 + 6.2/6.1.1/6.0.0):
     `androidapks.com` old-versions pages** — plain HTML, no JS gate. Pattern:
     `https://androidapks.com/<slug>/com-evozi-injector/old/` → per-version links
     `https://dl.androidapksfree.net/file/<20-hex>?e=<epoch>&s=<40-hex>`; regex
     `6\.\d\.\d` and grab the nearest dl link within ±300 chars. Verify `PK\x03\x04`.
     **apk.cafe** (`https://<slug>.apk.cafe/`) also works: the download page embeds
     `href="https://apk.cafe/go/?file_id=<id>&b=<base64url>"` where
     `b = base64.b64encode(signed filesincloud URL)` — decode `b` and curl the
     result directly.
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
- **NEW (2026-08-09): `androguard 4.1.4` is installed** (`/opt/venv/bin/pip install androguard`)
  — use it for binary AXML/ARSC instead of raw regex (a compiled AndroidManifest.xml
  has ZERO printable runs; regex finds nothing). Recipe:
  `from androguard.core.apk import APK; a = APK('app.apk')` then
  `a.get_activities()`, `a.get_package()`, and for intent-filters/deep-links:
  `xml = a.get_android_manifest_axml().get_xml_obj()` → `xml.iter('activity')` →
  iterate children for `intent-filter` → `data` elements carry `scheme`/`host`/
  `pathPattern` attrs. This is how HTTP Injector's deep links were recovered:
  `ConfigImportActivity` ↔ host `config.ehi.link` pathPattern `/.*` + `*.ehi`/
  `*.bin`/`*.enc` file intents; `DeepLinkActivity` ↔ scheme `httpinjector://`.
  **Gotcha:** `get_android_manifest_axml()` ALREADY returns an `AXMLPrinter` —
  wrapping it in `AXMLPrinter()` again raises `TypeError: a bytes-like object is
  required, not 'AXMLPrinter'`. Also `logging.disable(logging.CRITICAL)` first to
  silence its noisy debug output.
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
