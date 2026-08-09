# HTTP Injector 6.5.0 — APK hunt for the cloud-config fetch endpoint (2026-08-09)

Goal: find the base host for `/httpinjector/*` API paths so an 8-char cloud key
(`ed242a7S`) can be fetched and decrypted. Status at session end: **all pieces
found except the base host** — next probe target is `ehiapp.com` / `mycloudclient.com`.

## Downloading 6.5.0 (verified working)
- apkcombo serves 6.5.0 only as an `.apks` split bundle via the R2 signed-URL
  trick (see apk-hunting.md). `httpinjector_650.apks` = 69.8MB zip.
- Structure: `com.evozi.injector.apk` (12.4MB base), `config.arm64_v8a.apk`
  (native libs), `config.<lang>.apk` splits.
- **The base APK is PACKED**: `classes.dex` (21KB) is a DexHelper loader stub;
  the only real dex in base is the Meta ads SDK (`assets/audience_network/`).
  strings-scanning base dex = waste of time.

## Real code lives in `config.arm64_v8a.apk`
- `lib/arm64-v8a/libdatajar.so` (20.2MB) = packed dex. Its string table IS
  readable: RTTI class names (`Lcom/evozi/injector/views/ConfigImportActivity;`
  etc., with `\xef\xbe\xa0`-style obfuscation filler bytes) + **plaintext API paths**.
- `lib/arm64-v8a/libdexjniehi.so` (1.5MB) — "dex JNI ehi", only 1 ehi-ish string
  (obfuscated); libtunnelcore.so (51MB), libDexHelper*.so (packer), libevozi.so,
  libhst.so (tun2socks) — none carry the host.

## Strings found in libdatajar.so (the gold)
```
/httpinjector/attest_config   /httpinjector/backup   /httpinjector/config
/httpinjector/export_config   /httpinjector/import_config
/httpinjector/login           /httpinjector/servers  /iap/verification
User-Agent: Evozi-EHI/1.4.1\n\r\n     http://     https://   (bare builders)
```
- No full URL in the .so → host is assembled at runtime (builder strings `http://` + `https://`).
- No dex magic inside libdatajar.so (encrypted payload; string table only).

## Host probes (UA `Evozi-EHI/1.4.1`, both GET and POST tried)
| Host | Result |
|---|---|
| ehi.link | 404 — Next.js SPA, no /httpinjector API |
| config.ehi.link | 200 SPA shell for EVERY path (catch-all; not an API) |
| httpinjector.com | 404 GET / 405 POST — Next.js POST handler exists, no cloud paths |
| app.ehi.link | real server (Google 404 page) but no /httpinjector paths |
| ehi.li, api.ehi.link | DNS NXDOMAIN |

## Manifest deep links (androguard, base APK)
- `ConfigImportActivity`: VIEW/BROWSABLE on `http`+`https` `config.ehi.link` `/.*`
  (the app intercepts cloud-config links directly) + file patterns `*.ehi/.bin/.enc`.
- `DeepLinkActivity`: custom scheme `httpinjector`.

## resources.arsc (ARSCParser) — Firebase config still embedded in 6.5.0
- `firebase_database_url` = `https://http-injector.firebaseio.com`
- `google_storage_bucket` = `http-injector.firebasestorage.app`
- `project_id` = `http-injector`, `gcm_defaultSenderId` = `741730731635`,
  `google_api_key` = `AIzaSy…NCb8`, `google_app_id` = `1:741730731635:android:104d4c854204a2fe`

## Firebase state (all definitively probed 2026-08-09)
- RTDB: **423 "The Firebase database 'http-injector' has been deactivated"** on
  every path, with or without `?auth=`. Dead for good.
- Firestore REST: 403 "Cloud Firestore API has not been used in project http-injector".
- Storage bucket exists: 404 on `/<key>.ehi` objects, 400 on wrong path shape.
  (Did NOT try `alt=media` on the 404-shape paths — untested, low odds.)

## network_security_config.xml — THE backend clue
- `domain-config cleartextTrafficPermitted="false"` (HTTPS-only) for:
  **`ehiapp.com`** and **`mycloudclient.com`** (both includeSubdomains).
- These are the app's own pinned backends. The older session's "dead shells"
  verdict was plain-GET only; **`/httpinjector/*` paths + `Evozi-EHI/1.4.1` UA
  were never tried against them** — that is the next probe (in-flight at session end).

## Tooling notes
- androguard 4.1.4 installed in /opt/venv — pure python, no java needed:
  `APK('x.apk').get_activities()`, `.get_android_manifest_axml().get_xml_obj()`
  (iter `activity` → `intent-filter` → `data` attrs), `ARSCParser(bytes)` +
  `get_string_resources(pkg)` (returns **bytes of an XML dump** — write to file,
  then grep `<string name=...>`), `AXMLPrinter(raw).get_xml()` for
  network_security_config. Silence spam with `logging.disable(logging.CRITICAL)`.
- `res/raw/about` = EULA only; `res/raw/v2ray_config.json` = local v2ray template.
