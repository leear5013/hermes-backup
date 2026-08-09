# HTTP Injector cloud-config — session 6 findings (2026-08-09)

Continuation of the ehiapp.com probe campaign. Prior sessions established:
ehiapp.com apex = live Cloudflare-fronted JSON backend (see http-injector-cloud-api-probe.md).

## New verified facts (session 6)

### 6.4.1 APK is ALSO packed (unpacked-build lead DEAD)
- `httpinjector_641.apks` downloaded via apkcombo version-page r2 flow (68.7MB, 22 splits).
- Base `com.evozi.injector.apk`: `classes.dex` = **19,256 bytes** (DexHelper stub, same as 6.5.0).
- `config.arm64_v8a.apk` split contains `libdatajar.so` (18.8MB) — same plaintext string pool
  (all `/httpinjector/*` paths + `Evozi-EHI/1.4.1` UA), NO base host literal anywhere.
- Consequence: packed timeline spans ≥ 6.4.1 → 6.5.0. Unpacked build must predate 6.4.
- Assets: no config blobs (PublicSuffixDatabase, geoip/geosite, textmate editor files only).
- URL scan of 18.8MB libdatajar.so: 47 URLs, ALL third-party SDK (mullvad/adguard DOH list,
  vungle ads, googleapis, play.google) — zero Evozi-hosted literals.

### Hotshare = LAN tethering, NOT cloud config (false lead, closed)
- `HotshareService` / `HotshareActivity` strings in libdatajar.so.
- Context shows it's the hotspot/LAN sharing feature (FCM-paired service list).
- Do not chase it for cloud-config.

### mycloudclient.com = the live unprobed lead
- network_security_config.xml pins `ehiapp.com` + `mycloudclient.com` (both includeSubdomains,
  HTTPS-only, cleartext NOT permitted).
- All prior probing hit ehiapp.com; **mycloudclient.com was NEVER probed with
  `/httpinjector/*` paths + `Evozi-EHI/1.4.1` UA (GET/POST)**. This is the next probe.

### Cloudflare edge behavior taxonomy (confirmed)
- `/httpinjector/{config,servers,backup,import_config,export_config,attest_config}` → 405
  EMPTY body on GET/POST/HEAD + every Content-Type (urlencoded/text/octet/xml/protobuf/grpc+proto)
  + every header fuzz (CF-Access, x-api-key, Authorization, Referer/Origin, x-*-key, attestation…)
  = blocked at CF edge (worker/WAF with strict contract).
- `/httpinjector/login` + `/iap/verification` → fall through to origin: JSON 404
  `{"error":"Not found"}`, `Vary: rsc, next-router-*`, `Cf-Placement: remote-SIN`
  = Next.js App Router behind Cloudflare.
- PUT/PATCH/DELETE/OPTIONS on any path → 301 → www (never follow).
- `www.ehiapp.com` POST /httpinjector/config with CF-Access headers → **401
  `{"status":401,"error":"Missing required security headers"}`** — app-custom
  signed-request gate exists (NOT WordPress 403 that plain GET gets).
- All 43 guessed ehiapp.com subdomains → NXDOMAIN (api/config/cloud/c/app/v1/v2/m/…).
- config.ehi.link/<key> returns identical 200 Cloud-Config interstitial for ANY key
  (ed242a7S, aaaa1111, 0, x) — pathname is not validated server-side.
- httpinjector.com API mirror: dead (POST 405, GET Next.js 404 on all paths).
- ehi.link: Next.js SPA; /httpinjector/* 404; /config 200 (catch-all page).

### Wayback CDX
- ZERO captures of `/httpinjector*` on any host (httpinjector.com, ehiapp.com, ehi.link,
  mycloudclient.com, config.ehi.link, app.ehi.link, http-injector.com).
- config.ehi.link: exactly 1 snapshot (20250515, 301).
- No archive shortcut exists.

### APKCombo old-version download recipe (works)
1. `GET https://apkcombo.com/http-injector/com.evozi.injector/versions/` → lists only
   6.5.0 / 6.4.1 / 6.4.0 download links.
2. `GET https://apkcombo.com/http-injector/com.evozi.injector/download/phone-6.4.1-apk`
   → parse `href="/r2?u=<urlencoded R2 signed URL>"`.
3. `GET https://apkcombo.com/r2?u=...` with `Referer: https://apkcombo.com/` → 302 to
   `apks.<hash>.r2.cloudflarestorage.com/com.evozi.injector/6.4.1/<build>.apks`
   → save whole bundle. No JS-gate.

## Next actions (unfinished)
1. **POST-probe mycloudclient.com** `/httpinjector/config` (and friends) with
   `User-Agent: Evozi-EHI/1.4.1` + JSON body `{"key":"<8-char>"}`.
2. Decode attestation flow: arsc strings `attest_device` / `attest_failed` +
   `/httpinjector/attest_config` sits directly beside `/config` in the .so string pool
   → likely the 405 gate expects an attestation token obtained via
   `/httpinjector/attest_config` first (device challenge → token → /config with header).
3. Find a pre-6.4 APK (Softpedia / APKPure mirror) for the unpacked request builder.
