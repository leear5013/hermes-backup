# HTTP Injector cloud API — session 7 probe results (2026-08-09)

All probes: UA `Evozi-EHI/1.4.1`, key `ed242a7S`. Same-version facts confirmed for BOTH 6.4.1 and 6.5.0.

## mycloudclient.com — ELIMINATED (was the last unpinned host)
Plain nginx shell, plain-HTML 404 (NOT JSON — unlike ehiapp.com) on:
- `GET /` , `GET/POST /httpinjector/config`, `GET /httpinjector/login`
- `www.mycloudclient.com` same on all.
Not a JSON backend, not CF-fronted, no API. Both network_security_config-pinned hosts now fully probed:
ehiapp.com = live CF-fronted JSON API; mycloudclient.com = dead.

## ehiapp.com — full probe matrix (all /httpinjector/* paths)
| Layer | Behavior |
|---|---|
| `/httpinjector/login`, `/httpinjector/iap/verification` | JSON 404 `{"error":"Not found"}` — falls through CF to Next.js origin (Vary: rsc, Cf-Placement: remote-SIN) |
| `/httpinjector/config`, `servers`, `backup`, `import_config`, `export_config`, `attest_config` | **405 EMPTY body on GET+POST** — blocked at CF edge (worker route w/ strict contract) |
| PUT/PATCH/DELETE/OPTIONS any path | 301 → www.ehiapp.com (CF redirect rule) |
| POST directly to www.ehiapp.com | 401 JSON `{"status":401,"error":"Missing required security headers"}` |
| GET www.ehiapp.com | WordPress-style WAF 403 |

### Fuzzes that ALL still returned 405 (nothing budged)
- 14 header sets: CF-Access-Client-Id/Secret, x-api-key (arsc google key), x-app-version 6.5.0, X-Requested-With, x-ehi-key, x-config-key, Authorization: Bearer <key>, x-client-version 1.4.1, x-app-id com.evozi.injector, x-device-id, x-attestation, Referer/Origin config.ehi.link + ehiapp.com.
- Content types: urlencoded, text/plain, octet-stream, xml, x-protobuf, grpc+proto.
- Paths without /httpinjector prefix on ehiapp.com: `/config`, `/api/config`, `/config/<key>`, `/get_config`, `/fetch_config`, `/share_config`, `/cloud`, `/s/<key>`, `/import/<key>`, `/api/httpinjector/config`, `/ehi/config/<key>`, `/configs/<key>`, `/download/<key>` → all plain Next.js 404.
- All 43 common subdomains (api, config, cloud, c, app, v1/v2, m, mobile, srv, server, backend, gateway, ehi, admin, cdn, static, files, data, db, test, dev, staging, old, beta, premium, pro, link, share, import, export, upload, download, s/d/k/key/get/go/cc, cloudconfig) → NXDOMAIN (Errno -5).
- Other hosts as API mirrors: httpinjector.com POST → 405 (GET → Next.js 404), ehi.link → Next.js 404.

## config.ehi.link — key-independent
`GET /<key>` returns the IDENTICAL 200 interstitial for ed242a7S / ed242a7S2 / aaaa1111 / 0 / x — no server-side key validation, pure client-side redirect page.

## Firebase project http-injector — final sweep (nothing new)
- RTDB: 423 permanently deactivated (known).
- **Firestore REST** `projects/http-injector/databases/(default)/documents` → **403 "Cloud Firestore API has not been used in project http-injector"** — never enabled.
- **Storage bucket `http-injector.firebasestorage.app`** exists but 404s `/<key>.ehi` objects.
- Legacy arsc values: firebase_database_url=https://http-injector.firebaseio.com, project_id=http-injector, gcm_defaultSenderId=741730731635, google_app_id=1:741730731635:android:104d4c854204a2fe.

## GitHub code search — 0 public hits
- Auth: `/data/.git-credentials` token works ONLY as `Authorization: Bearer <token>` (the `token <t>` scheme → 401).
- Queries `Evozi-EHI`, `attest_config`, `httpinjector/config`, `httpinjector/export_config`, `http-injector firebaseio` → 0 results (limit 30 search calls/hr; occasional 503 → retry).

## Remaining open (next session)
- Device-attestation flow: arsc strings `attest_device` / `attest_failed` + endpoint `/httpinjector/attest_config` sit beside /config in the libdatajar.so string pool. Hypothesis: Play Integrity (or Evozi's own challenge) attestation precedes any config fetch → that's the 405/401 gate.
- The base host is STILL not a literal in the .so string pool of either 6.4.1 or 6.5.0 (verified by direct context dump: `/httpinjector/*` block is standalone, adjacent strings are unrelated paths like `/pagead/*`); it is assembled at runtime (string building with `%s` fragments, or dex payload code that was never plaintext-recovered).
- libdexjniehi.so obfuscated strings (nere+hejc, Gleve, Mhhace…) — NOT a Caesar/ROT shift, NOT keyboard-adjacent; it's the DexHelper JNI's own obfuscation, junk for our purposes. Don't chase again.
- HotshareService/HotshareActivity = LAN hotspot tethering feature, NOT cloud config — dead lead.
