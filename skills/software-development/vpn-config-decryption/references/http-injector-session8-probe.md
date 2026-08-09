# HTTP Injector cloud-config — session 8 (2026-08-09): CF edge taxonomy + AES transport

Follow-up to session7-probe.md. All probes against `ehiapp.com` (the only surviving
network_security_config-pinned host; mycloudclient.com = dead nginx, eliminated).

## Method sweep on /httpinjector/config (new taxonomy)

| Method | Result | Interpretation |
|---|---|---|
| GET / POST / HEAD | 405 EMPTY body, NO `Allow` header | CF edge method-block |
| TRACE | 405 with full HTML `<title>405 Not Allowed</title>` | different edge rule path |
| PUT / PATCH / DELETE / OPTIONS / MKCOL / PROPFIND / REPORT / QUERY / SEARCH | 301 → `www.ehiapp.com` | CF www-redirect; www = WAF 403 page |
| CONNECT | 400 (CF default) | — |

Refinement of the earlier "CF Worker strict contract" hypothesis: the empty-body
405 with no `Allow` header is **Cloudflare edge behavior (WAF/security rule on
methods), not an origin route contract**. The origin never sees GET/POST on this
path. TRACE getting an HTML 405 while GET/POST get empty-body 405 proves the
block is at the edge, not the app.

Path variant probe: `/httpinjector/config/ed242a7S` → **404 JSON `{"error":"Not found"}`**
(falls through to origin — route exists but no subpath match). Same for
`/httpinjector/config2`, `/httpinjector/xyz`. So: bare `/config` = edge-blocked,
anything deeper = origin JSON 404. The edge rule matches exactly the known path
list (`/httpinjector/{config,attest_config,servers,backup,import_config,export_config}`).

Header sweep on GET /config (14 sets: X-API-Key, Authorization Bearer/<key>,
X-Attestation, X-App-Id, Origin/Referer config.ehi.link, Accept json/text…) → ALL 405.
Query-param variants `?key=/?code=/?id=/?hash=` → ALL 405. Form-encoded POST bodies → 405.
→ The edge block is method-based and content-agnostic. Either the app's real
request carries something the edge still accepts (impossible to guess blind) or
the /httpinjector/ API was retired from the edge config for new installs.

## config.ehi.link catch-all (final)

Every path returns the IDENTICAL 200 "Cloud Config" interstitial:
`/`, `/ed242a7S`, `/api/config/ed242a7S`, `/config/ed242a7S.json`, `/get/ed242a7S`,
`/key/ed242a7S`, `/httpinjector/config`. Zero server-side key validation — the SPA
is purely cosmetic; the actual fetch + decrypt happens inside the APK
(ConfigImportActivity deep-link). No JS bundle on the page performs a fetch.

## AES-CBC config transport (from libdatajar.so string pool, 6.5.0 + 6.4.1 identical)

Confirmed from the plaintext string table inside the packed split lib:

- `AES/CBC/NoPadding` AND `AES/CTR/NoPadding` both present
- Constants: `CONFIG_AES_KEY`, `OLD_CONFIG_AES_KEY`, `IOS_CONFIG_AES_KEY`,
  `AES_BLOCK_SIZE`, `CLIENT_KEY`, `ENCRYPTED_CPM_KEY`, `CLOUD_SAVE`
- Models: `com/evozi/injector/model/EncryptedApi` (+ callback
  `ServersActivity$…$onEncryptedResponse`), `ExportConfig`, `ImportConfig`,
  `ConfigShell`, `ConfigOption`, `ConfigJsonDnstt`, `LogicalServers`, `IAP`,
  `HttpObfs`, `Plugin`, `Profile`

→ The cloud API returns an **AES-encrypted blob** (EncryptedApi), key selected by
CONFIG_AES_KEY / OLD_CONFIG_AES_KEY / IOS_CONFIG_AES_KEY constants. **The key
VALUE is NOT in the string pool** (it lives in the DexHelper-encrypted dex inside
the same .so). Red herrings in the same pool: `OMInjector`/`OMSDK` = OpenMeasurement
ads SDK; the giant hex blobs (00C6858E…, FFFFFFFFFFFFFFFF… = RFC 3526 DH group) are
SSH lib (trilead) / TLS constants, not the AES key.

## String-table technique (works even on packed dex)

The packed libdatajar.so contains NO dex magic — the DexHelper payload is
encrypted — but the full dex **string pool survives as contiguous plaintext**,
uleb128-length-prefixed (e.g. `\x1b/httpinjector/config`, 0x1b=27). Technique:
regex `[\x20-\x7e]{4,}` over the raw .so finds the whole pool; constants like
`CONFIG_AES_KEY` appear alphabetically in a giant string run — dump ±300 bytes
around a hit to see neighbors. `classes.dex`/`classes3.dex` NAME strings exist at
fixed offsets but the dex data itself is unreachable. 6.4.1's pool is byte-identical
for the API paths → same build-era backend.

## Still open (2026-08-09 EOD)

- The edge accepts only the app's real request shape; blind fuzzing exhausted.
- Device attestation (`/httpinjector/attest_config` + `attest_device`/`attest_failed`
  strings) is the leading hypothesis for what precedes config fetch — Play Integrity
  or Evozi's own challenge, only issuable on a real device.
- AES key value unrecoverable without unpacking the DexHelper payload.
- Practical path for the bot: share-code → config.ehi.link page tells users nothing
  usable; in-app fetch is required → cloud-config engine for @RasdAgent_bot stays
  "not implementable server-side" unless the attestation flow is solved on-device.
