# HTTP Injector Cloud Configs — recon status (2026-08-09, session 2)

Goal: resolve a short cloud-config key (e.g. `ed242a7S`, user-provided) to the
decryptable .ehi file. **The download endpoint is STILL not located**, but the
resolver page is now fully understood and the old Firebase store is confirmed
dead. This file records verified probe results so the next session doesn't
re-probe dead ends.

## What a "cloud config" is
HTTP Injector (Evozi) lets users share configs by short key instead of the raw
.ehi file. The app's "Import Config" page accepts either the full share link or
just the key (≤10 chars, `maxlength="10"` input).

## config.ehi.link — fully deobfuscated (2026-08-09, node mock-DOM run)
- Page (`https://config.ehi.link/`, 5.5KB HTML shell, every path returns the
  SAME shell — it is a pure SPA, no server-side key lookup):
  - `<input id="ehiConfigKey" maxlength="10" readonly value="">` — server does
    NOT echo the key; page reads it from the URL itself.
  - JS is obfuscator.io string-array (`U()`/`I()` shuffle, custom base64 +
    RC4-ish transform, `0x815a8` rotation checksum). **It runs as-is in node**
    with a mocked DOM — no need to port the decoder.
  - `getConfigKey()` → `document.getElementById('ehiConfigKey').value =
    window.location.pathname.replace(/[^\w\s]/gi, '')`. **THE KEY IS THE URL
    PATH SEGMENT.** `config.ehi.link/ed242a7S` → key `ed242a7S`. (Instrument
    `location` with getters to see which property is read; `pathname` is the
    one.)
  - `importEvoziConfig()` → sets global `window['ehiConfigKey']` string (an
    intent/redirect value, `'SQrlh'` deobfuscates to a Google-Play-app-link
    style redirect, `app.ehi.link`-adjacent). **The page performs NO fetch** —
    it is purely a "copy the key / open the app" interstitial. The config
    download happens inside the APK.
- Implication: server-side there is nothing to find on this domain. The fetch
  URL lives in the APK (`com.evozi.injector`). **Next step remains: strings-scan
  the dex for the cloud fetch endpoint** (`cloud`, `getconfig`, `config.ehi`,
  `ehi.link`, `.ehi` URL patterns).

## Old Firebase store — CONFIRMED DEAD (2026-08-09)
Both APKs embed `https://http-injector.firebaseio.com` (the old cloud store).

| Probe | Result |
|---|---|
| `https://http-injector.firebaseio.com/.json` and `/<KEY>.json`, `/configs/<KEY>.json`, `/cloud/<KEY>.json` | **423 Locked** (project disabled/locked — data unrecoverable) |
| `http-injector.firebasedatabase.app/*` | DNS NXDOMAIN (project deleted) |
| `http-injector-default-rtdb.firebaseio.com/*` | 404 (wrong project or never existed) |
| `http-injector-default-rtdb.firebasedatabase.app/*` | DNS NXDOMAIN |
| `https://firebasestorage.googleapis.com/v0/b/http-injector.appspot.com/o` | 412 Precondition Failed (bucket listing locked) |

Conclusion: 8-char keys were Firebase-era; that store is gone (Google disables
inactive projects → 423). Old keys returning "invalid-link" on the modern
ehi.link panel = never migrated, not merely expired.

## ehi.link / Wayback findings
- CDX has hundreds of archived `ehi.link/<8-char-key>` links (2022–2025, e.g.
  `01EPfckP`, `0af7Vzy1`, `0fGjOSzU`, `1AUS00w4`) — ALL archived as **301
  redirects** (stubs, no content). `ed242a7S` itself has NO snapshots.
- Modern ehi.link panel (`/httpinjector`, `/iap`, `/api/ehi`, `/api/config`,
  `/api/distribution/<uuid>`) → 404 for any key/id format; random-UUID probes
  confirm only the Next.js catch-all (`/httpinjector?x=`) returns 200 (HTML
  shell, client-side rendered).

## mycloudclient.com / ehiapp.com — REVISED (session 4, 2026-08-09)
These two domains came from the APK's `network_security_config.xml`:
- `mycloudclient.com` — **WAF 403 on EVERYTHING** (WordPress-style block page,
  `<!doctype html><!--[if lt IE 7]>…`). Blocked at edge, not dead. Do not
  re-probe from this VPS.
- `ehiapp.com` **apex** — REAL Cloudflare-fronted API server (session 4
  evidence, ehi_apex_evidence.txt): `Server: cloudflare`, JSON bodies:
  - `GET/POST /httpinjector/login` → **404 `{"error":"Not found"}`** (app JSON, not a WAF page)
  - `GET/POST /httpinjector/iap/verification` → **404 `{"error":"Not found"}`**
  - `/httpinjector/config`, `/servers`, `/attest_config`, `/import_config`,
    `/export_config`, `/backup` → **405 on GET AND POST** (endpoint exists,
    method not allowed — Cloudflare `405` with empty body; exact verb unknown)
  - `PUT`/`OPTIONS` on any path → 301 to www (Cloudflare rule); `www.ehiapp.com`
    = 403 WAF block page (and 405 w/ Next.js Vary headers on /httpinjector/config)
  - `/httpinjector/config/<KEY>` → 404 JSON (key not in path)
- **app.ehi.link = Firebase Dynamic Links router, NOT an API** (session 4):
  - `/config` → 200 → Play Store page for `com.evozi.injector` (`pcampaignid=fdl_short`)
  - unknown paths → 400 "Invalid Dynamic Link" / 404 "Dynamic Link Not Found"
  - The config.ehi.link page's `importEvoziConfig()` sets
    `window.location = "https://app.ehi.link/config"` (deobfuscated via node
    mock-DOM, ehi_deob4.js) — i.e. the share flow is: config.ehi.link page →
    Firebase dynamic link → app deep link → ConfigImportActivity → in-app fetch.
  - The in-app fetch host is STILL NOT FOUND; `/httpinjector/*` paths live in
    libdatajar.so string table (packed dex) with NO base URL — host built at
    runtime in encrypted bytecode. 6.5.0 base classes.dex = packer stub, so the
    host is NOT recoverable by static scan of the current build; an unpacked
    legacy build or runtime interception (mitmproxy on a real device) is the way.
- `www.ehi.tips` / `ehi.tips` (from resources.arsc) — **DNS NXDOMAIN** (dead).
  Do not re-probe.

## Next steps (when resumed)
1. **The current-APK strings-scan is DONE and exhausted (2026-08-09):** 6.5.0's base
   `classes.dex` is a 22KB PACKER stub (DexHelper/ACFNAME — real code encrypted in
   payload), and `resources.arsc` embeds only the dead Firebase URL +
   `https://httpinjector.com`. apkcombo old-versions only goes back to 6.4.0 (also
   likely packed — it's the same build family). **Remaining leads:** (a) an UNPACKED
   5.6.4-era APK (Softpedia `mobile.softpedia.com/apk/http-injector/5.6.4/` — may
   still 403 from this VPS; apkpure.net/br has 6.3.6), (b) runtime interception
   (mitmproxy) of the app's cloud-import traffic, (c) `app.ehi.link` (the
   importEvoziConfig intent target) for a web view/redirect revealing the fetch
   pattern.
2. Once .ehi bytes are fetched, decrypt with HTTPINJECTOR.py engine
   (AES-CBC→AES-128→XXTEA, see SKILL.md).

## Session-3 verified probes (2026-08-09, sandbox reset rebuilt the hunt)
- **Firebase RTDB final answer** — every path incl `?auth=AIzaSy…` and
  `?print=pretty`: `423 {"error":"The Firebase database 'http-injector' has been
  deactivated."}` — the project is DISABLED by Google, not just locked. Data is
  unrecoverable; stop probing.
- **`httpinjector.com`** (official site, embedded in 6.5.0 resources.arsc) —
  Next.js shell like ehi.link; `/cloud`, `/cloud/`, `/config`, `/api`,
  `/api/cloud`, `/api/config`, `/download`, `/getconfig`, `/cloud-config`,
  `/cloudconfig` → ALL 404 (client-side SPA, no server cloud API). Do not
  re-probe.
- **6.5.0 APK is packed** — base `classes.dex` = 21,992 bytes stub with
  `DexHelper`, `###ACFNAME###`, `Iii1Iii1IIIi1`; only readable code is the
  Meta Audience Network ad SDK (`assets/audience_network/*.dex`). The dex
  strings-scan approach that worked for NetMod does NOT apply here.
- **apkcombo old-versions** (`/http-injector/com.evozi.injector/old-versions/`)
  only lists 6.4.0 / 6.4.1 / 6.5.0 (links `.../download/phone-6.4.1-apk` etc.) —
  no unpacked legacy build available there.
- **APKMirror 6.5.0 is JS-gated** (the `/download/?key=<40-hex>` URL 302s to the
  HTML shell with `?redirected=t` — no APK bytes). Use apkcombo instead (below).

## apkcombo /r2?u= download (VERIFIED 2026-08-09 — HTTP Injector 6.5.0 .apks)
apkcombo now serves files from Cloudflare R2, NOT the old pureapk `d?u=` CDN.
- App page `/http-injector/com.evozi.injector/` → version list. The version page
  `/download/apk` (or `/download/apk-6-4-1` etc.) contains links of the form
  `href="/r2?u=<urlencoded-encoded-url>"`.
- The `u` param is DOUBLE-urlencoded: `urllib.parse.unquote(unquote(u))` →
  `https://apks.39b7cb94d40914bac590886981b0ed6e.r2.cloudflarestorage.com/<pkg>/<ver>/<code>.<hash>.apks?response-content-disposition=…&X-Amz-Algorithm=…&X-Amz-Signature=…` (signed, time-limited).
- Fetch `https://apkcombo.com/r2?u=…` with a browser UA + Referer apkcombo.com →
  follows to R2, content-type `application/xapk-package-archive` (or
  `application/vnd.android` for .apk). Verify magic `PK\x03\x04`.
- 6.5.0 ships ONLY as `.apks` (split bundle, 69.8MB): entries =
  `com.evozi.injector.apk` (12.4MB base — the packed one), `config.<abi>.apk`
  (arm64_v8a / armeabi_v7a native splits), `config.<lang>.apk`, `manifest.json`,
  `icon.png`. Extract the base APK with python zipfile and scan THAT.
- Pitfall: saving the download with a filename derived from the URL tail gives a
  garbage name (the tail is `…aws4_request&X-Amz-Signature=…`); always save with
  an explicit fixed name.

## Pitfalls
- `config.ehi.link/<KEY>` page is identical for EVERY key — the key is read
  from `pathname` client-side. A 200 here proves nothing about key validity.
- The Next.js ehi.link wrapper's "invalid-link" message is client-side; the raw
  fetch layer is server-side / app-side.
- **Don't treat WAF blocks as "dead"** — mycloudclient.com and www.ehiapp.com
  are 403 WAF-blocked from this VPS, while ehiapp.com apex serves real JSON API
  responses; a Cloudflare 405-on-every-method for `/httpinjector/*` means the
  path EXISTS with a different required verb, not that it's gone.
- `cloud.httpinjector.com`, `mycloudclient.com`, `ehiapp.com`, and
  `httpinjector.com` cloud paths — WAF-blocked/405/Next.js-SPA respectively;
  the ONLY live-looking API is ehiapp.com apex (JSON error bodies) but its
  config endpoint's exact verb/param shape is still unknown (405 on GET+POST).
- **Current HTTP Injector APKs are packed** — before spending a scan cycle on a
  fresh version's dex, check `classes.dex` size first: ~22KB + DexHelper strings
  = packer stub, strings-scan useless; go for resources.arsc or an older
  unpacked build instead. The `/httpinjector/*` API paths + UA
  `Evozi-EHI/1.4.1` come from the packed dex's string table in
  `libdatajar.so` (arm64 split), but the base host is built at runtime in the
  encrypted bytecode — static scan cannot recover it.
- When deobfuscating obfuscator.io JS: run it in node with mocked
  `document`/`window`/`navigator` rather than porting the decoder — the
  rotation loop (`0x815a8` checksum) is deterministic but pointless to
  re-implement. Instrument `window.location` with property getters to discover
  which URL field the script reads (pathname in this case).
