# HTTP Injector cloud-config API probe — 2026-08-09

Goal: resolve 8-char share key (`ed242a7S`) to a fetch endpoint and decrypt the config.
Status: endpoint narrowed to `ehiapp.com` apex (`/httpinjector/config` exists, returns 405 for
every method/body tried); exact route method + params still open. Do NOT re-probe the dead
domains below — table is the ground truth.

## APK 6.5.0 structure (apkcombo `.apks` bundle, 69.8 MB)
- Zip of split APKs: `com.evozi.injector.apk` (base, 12.4 MB) + `config.arm64_v8a.apk` + density splits.
- Base APK: `classes.dex` = **22 KB packer stub** (DexHelper); `assets/audience_network/*.dex` = Meta ads SDK (ignore); `resources.arsc` 830 KB; `res/raw/v2ray_config.json`.
- `config.arm64_v8a.apk` native libs: **`libdatajar.so` 20 MB = the packed dex** (plaintext string pool: class names `Lcom/evozi/injector/views/ConfigImportActivity;`, API paths, UA, all app strings), `libdexjniehi.so` 1.5 MB (JNI bridge, few strings), `libevozi.so`, `libhst.so`, `libtunnelcore.so` 51 MB, `libDexHelper.so` (packer).
- Extract everything with python zipfile (no `unzip` binary on VPS).

## libdatajar.so string-table harvest (the app's real code)
- API paths (all relative, no host): `/httpinjector/attest_config`, `/httpinjector/backup`, `/httpinjector/config`, `/httpinjector/export_config`, `/httpinjector/import_config`, `/httpinjector/login`, `/httpinjector/servers`, `/iap/verification`.
- `User-Agent: Evozi-EHI/1.4.1` inside an HTTP header block (`\nUser-Agent: ...\n\r\n`).
- NO base host/URL anywhere in the .so (only `http://` + `https://` builder fragments, DoH domains, ads SDK URLs). Host is assembled at runtime (resource string or code) — still the open question.
- `http-injector.firebaseio.com` appears ONLY in resources.arsc, not in the .so.

## Manifest (binary AXML via androguard — see apk-hunting.md for the API)
- `ConfigImportActivity` intent filters: (a) VIEW/BROWSABLE, data scheme `content|file`, mimeType `*/*`, pathPattern `.*\.ehi|.*\.enc|.*\.bin` (file import); (b) **host `config.ehi.link`, scheme `http|https`, pathPattern `/.*`** (deep link — the app opens `https://config.ehi.link/<key>` directly, key = pathname).
- `DeepLinkActivity`: scheme `httpinjector` (custom scheme).
- package `com.evozi.injector`, versionName 6.5.0, versionCode 243.

## resources.arsc (ARSCParser → bytes of `<resources><string ...>` XML; write to file, grep)
- `firebase_database_url` = https://http-injector.firebaseio.com (DEAD, see probes)
- `google_storage_bucket` = http-injector.firebasestorage.app; `project_id` = http-injector; `gcm_defaultSenderId` = 741730731635; `google_app_id` = 1:741730731635:android:104d4c854204a2fe
- `device_attest_failed` string mentions **`www.ehi.tips/ccaf`** (new domain; NXDOMAIN from this VPS)
- Cloud strings: `cloud_config_key`, `cloud_config_not_found` ("Config not found, please make sure your config key is correct"), `cloud_config_not_available` ("no longer available. It has either expired or removed"), `config_key_url_emoji`, `cloud_import_failed`

## network_security_config.xml (AXMLPrinter)
- Pins `ehiapp.com` + `mycloudclient.com` (includeSubdomains, `cleartextTrafficPermitted=false` = HTTPS-only) → these are the app's real backend domains. Base-config allows cleartext elsewhere.

## Dead-end probe table (do not re-probe)
| Target | Result |
|---|---|
| `https://http-injector.firebaseio.com/.json` (+any path/auth param) | **423** body `The Firebase database 'http-injector' has been deactivated.` — project deleted/locked by owner, unrecoverable |
| `https://firestore.googleapis.com/v1/projects/http-injector/databases/(default)/documents/...` | 403 `Cloud Firestore API has not been used in project http-injector` |
| `https://firebasestorage.googleapis.com/v0/b/http-injector.firebasestorage.app/o/<key>.ehi` | 404/400 (bucket exists, empty) |
| `http-injector.firebasedatabase.app` | DNS NXDOMAIN (project deleted) |
| `www.ehi.tips` | DNS NXDOMAIN from VPS (string resource only) |
| `httpinjector.com/*` | Next.js site; 404 on all cloud paths; 405 on POST |
| `config.ehi.link/*` | catch-all SPA: same 5.9 KB "Cloud Config" interstitial for EVERY path incl. `/httpinjector/config` |
| `ehi.link/*`, `app.ehi.link/*` | Next.js panel / Firebase Dynamic Links (below) |
| `ehiapp.com` apex root | 200 empty body (Cloudflare) |
| `www.ehiapp.com` anything | 403 WordPress WAF block page (oldie HTML) |
| `mycloudclient.com` anything | 403 WAF (first probe round showed nginx 404 — inconsistent; treat as not-the-API) |

## Live-ish: ehiapp.com apex (`/httpinjector/*` routes exist)
- GET/POST on every `/httpinjector/*` route → **405** (Cloudflare). PUT/PATCH/DELETE/OPTIONS → **301** → `www.ehiapp.com` (then WAF 403).
- `GET /httpinjector/login` and `/httpinjector/iap/verification` → 404 JSON `{"error":"Not found"}` — proves a real JSON app server behind Cloudflare (not a static shell).
- Tried POST bodies: JSON `key|config_key|code|configKey` (single + combined), urlencoded, raw text/plain, hex, octet-stream, protobuf CT; GET query `?key=...`; header auth variants (X-API-Key, Bearer, X-Firebase-Api-Key); browser UA + Origin — ALL 405. Likely needs: specific POST schema, attestation/signed params, okhttp TLS fingerprint, or a different subdomain.
- CF headers present: `Cf-Placement: remote-SIN`, `CF-RAY` — the apex is behind Cloudflare.

## app.ehi.link = Firebase Dynamic Links (the import button's target)
- `importEvoziConfig()` in the config.ehi.link page JS (obfuscator.io; run in Node with mocked `document` + `window` Proxy) does `getElementById('ehiConfigKey')` then sets `window.location = "https://app.ehi.link/config"` — **no key in the URL**; the key lives only in the page's readonly input (maxlength=10) for copy-paste.
- `https://app.ehi.link/config` → 200 → redirects to `play.google.com/store/apps/details?id=com.evozi.injector&pcampaignid=fdl_short` (FDL short link). `?link=`/`apn=` params → 400 "Invalid Dynamic Link". Any unknown path → 404 "Dynamic Link Not Found".
- Identification: FDL always serves HTML titled "Invalid Dynamic Link" / "Dynamic Link Not Found".

## Share flow (as reconstructed)
User opens `https://config.ehi.link/<KEY>` → interstitial page shows key (pathname) → either copies it into the app's Import page, or taps Open & Import (FDL → Play Store/app). If the app is installed, Android delivers `config.ehi.link/<KEY>` to `ConfigImportActivity` directly (manifest filter) — the app then must call the config API with the key. That call's endpoint/params remain the open question.

## Probe taxonomy (Cloudflare-fronted targets — general lesson)
- 405 on ALL methods incl. GET = route registered but request shape wrong, OR CF default for an edge rule.
- 301 apex→www + WAF 403 on www = apex serves the app, www is a parked/blocked host; never follow the redirect for probing.
- Firebase Dynamic Links identified instantly by the "Invalid Dynamic Link" HTML.
- RTDB 423 body names the database + "deactivated" = owner deleted/locked the project; an API key cannot resurrect it.
- Session probe scripts live in `/data/workspace/ehi_*.py` (may be wiped on sandbox reset; patterns above are the durable part).

## Session-5 addendum (later 2026-08-09): ruled out + new leads
- **Subdomain sweep: ALL ehiapp.com subdomains NXDOMAIN** — api, config, cloud, c, app, api1/api2, v1/v2, m, mobile, srv, server, backend, gateway, ehi, admin, cdn, static, files, data, db, test, dev, staging, old, beta, premium, pro, link, share, import, export, upload, download, s/d/k/key/get/go/cc, cloudconfig. Only apex + www have DNS. Do NOT re-sweep.
- **www.ehiapp.com direct POST → 401 `{"status":401,"error":"Missing required security headers","code":401}`** (JSON, NOT the WordPress 403 that GET gets). Sending CF-Access-Client-Id/Secret does NOT satisfy it — the required headers are something else (signed-request / app-custom gate). Open lead.
- **Backend stack ID: Next.js App Router** — JSON-404 responses carry `Vary: rsc, next-router-state-tree, next-router-prefetch, next-router-segment-prefetch`, `Cache-Control: private, no-cache, no-store`, `Cf-Placement: remote-SIN`. `{"error":"Not found"}` is Next.js's default API-route 404. **Layer split:** `/httpinjector/login` + `/iap/verification` FALL THROUGH Cloudflare to the Next.js origin (JSON 404 = no such route at origin), while ALL `/httpinjector/*` (config, servers, backup, import/export, attest) → **405 EMPTY body = blocked at the CF edge** (worker/WAF rule with a strict contract), not by the origin. Different failure shapes = different layers.
- **Content-Type fuzzing on /config:** urlencoded, text/plain, octet-stream, xml, protobuf, grpc+proto → all 405. Header fuzz (x-app-version, x-api-key, X-Requested-With, x-ehi-key, Authorization Bearer, x-client-version, x-app-id, x-device-id, x-attestation, Referer/Origin) → all 405. Apex path fuzz without the /httpinjector prefix (e.g. /config, /cloud, /s/<key>) → all Next.js 404.
- **httpinjector.com as API mirror: dead.** POST /httpinjector/config, /config, /api/config, /ehi/config, /config/<key>, /c/<key> → 405; GET → Next.js 404. Same for www.httpinjector.com and ehi.link.
- **Wayback CDX: ZERO `/httpinjector*` captures on any host ever** (query form `url=<host>*httpinjector*` path-matches; checked httpinjector.com, ehiapp.com, ehi.link, mycloudclient.com, www.httpinjector.com, config.ehi.link, app.ehi.link, http-injector.com). config.ehi.link has exactly ONE snapshot (20250515, 301). httpinjector.com's 207 snapshots = Next.js chunks + about/privacy/terms only. The cloud API was never archived — no wayback shortcut to the old endpoint.
- **Attestation hypothesis strengthened:** arsc strings `attest_device`, `attest_failed` + endpoint `/httpinjector/attest_config` sitting beside /config in the .so string pool. The 405 contract likely needs a device-attestation flow first (Play Integrity or Evozi's own challenge) — consistent with www's "Missing required security headers" 401.
- **apkcombo old versions: 6.4.1 downloaded (68.7 MB .apks) via the same r2 chain** (`/download/phone-6.4.1-apk` → `/r2?u=<double-urlencoded>` → R2, `application/xapk-package-archive`). The `/versions/` page lists ONLY 6.4.0/6.4.1/6.5.0 — no older unpacked build available from apkcombo. **Extraction of the 68 MB .apks FAILED with `OSError: [Errno 28] No space left on device` on `/data/workspace`** (500 MB budget exhausted by accumulated probe artifacts) — extract large bundles to `/opt` or `/tmp` (1.8 TB overlay) going forward.
