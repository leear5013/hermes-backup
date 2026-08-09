# HTTP Injector cloud-config — Session 9 (2026-08-09) — lead closures

Context: 6.4.1 + 6.5.0 both DexHelper-packed. `network_security_config.xml` pins ehiapp.com + mycloudclient.com. Goal this session: pin the base URL / request shape for `/httpinjector/config`. Result: **several leads CLOSED for good; the app's request shape is unreachable blind.**

## 1. UA template lead FALSIFIED — no base host literal exists in libdatajar.so (both versions)
- Hypothesis: `\nUser-Agent: Evozi-EHI/1.4.1\n\r\n` was the tail of a hand-built HTTP request template with the base URL adjacent in the string pool.
- **Verdict: FALSE.** The UA's string-table neighbors are `GlideException#logRootCauses`, `The InputStream implementation is buggy`, `There was 1 root cause`, `method code index:` — i.e. it sits in a generic dump of debug/format strings, NOT a request builder. The exact same block appears byte-identical in 6.4.1 and 6.5.0 libdatajar.so.
- **Exhaustive URL scan of the whole 20MB .so (both versions): exactly ONE full URL** — `https://dns.mullvad.net/dns-query` (a DoH resolver for the VPN's DNS features). `http://` and `https://` exist ONLY as bare scheme fragments (`http://` / `https://` constants, no host). No `%s`-template containing a host. → **the base host is 100% runtime-constructed** (string concat in the DexHelper-encrypted dex — unreachable). Stop scanning the .so for the host.

## 2. libdexjniehi.so strings are NOT a cipher — closed with proof
Tested on the obfuscated-looking strings (`nere+hejc`, `gki+bkvp+ej`njm+NjmHmf`, `gehhkg`, `wpvhaj`, `wtvmjpb`…):
- Caesar shift over ±13 → no readable words; keyboard-adjacent mapping (QWERTY both directions) → nonsense; Vigenere key derivation vs `http+inject` target → key deltas are non-repeating (20,15,2,11,1,9,0,2). 
- Verdict: `nere+hejc+...` = obfuscated class-name pool (DexHelper JNI internals, `,_H...?-X` wrappers), not encrypted strings. libdexjniehi.so = the DexHelper loader JNI, not the ehi-cloud bridge. **Rabbit hole — do not reopen.**

## 3. config.ehi.link SPA — full JS deobfuscation, fully static
- Inline obfuscator.io-style script: array-rotation `U()` + custom base64→RC4-ish decoder `I()`. `importEvoziConfig()` decodes to a single statement: `window["location"] = "https://app.ehi.link/config"` — **STATIC URL, carries NO key, performs NO fetch**. The page is a pure interstitial (input `#ehiConfigKey` maxlength=10, copy button, "Open App & Import" button). Key = pathname, validated nowhere server-side (every path returns the identical 200 page).
- Technique that worked (Node, no npm deps): extract inline `<script>`, run under `eval` with a **Proxy-based `window` shim that logs every property set**, plus stub `document` (`getElementById`/`querySelector`/`createElement` returning `{value, setAttribute, addEventListener}`). First errors were `document is not defined` / `document[(b()+b())] is not a function` — the shims needed getElementById + a Proxy, then the assignment was captured. Complements the existing python deobfuscate_obfuscatorio.py for pages where you just want the side-effect (location assignment).
- **Manual `Host:` header pitfall:** setting `Host: ehiapp.com` explicitly in urllib's headers → every request 301s (CF redirect loop). Let urllib set Host from the URL; only override if the probe needs a different vhost.

## 4. Probe matrix re-run on ehiapp.com (all UA `Evozi-EHI/1.4.1`)
- `/httpinjector/xyz`, `/httpinjector/`, `/config2`, `/anything/at/all` → 404 JSON `{"error":"Not found"}` (origin). `/httpinjector/config` + friends → **405 EMPTY, no Allow header, on GET/POST/HEAD = Cloudflare EDGE method-block** (WAF rule matching exactly the known path list); TRACE → full HTML 405; PUT/PATCH/DELETE/OPTIONS/REPORT/QUERY/SEARCH/PROPFIND/MKCOL → 301 → www; CONNECT → 400. `/httpinjector/config/<key>` (path-param form) → 404 JSON (falls through — the edge rule matches the bare paths only).
- 14 header sets (X-API-Key, Authorization Bearer/raw, X-Client-Id, X-Platform, X-Attestation, Origin/Referer config.ehi.link…) + query params `?key/?code/?id/?hash` + urlencoded/form/octet/text bodies on POST → ALL 405. Content-agnostic, method-based block.
- `/httpinjector/attest_config` → 301 (not in edge block list, goes to www) — no attestation response obtainable.
- GitHub code search (Bearer token, 30/hr): `Evozi-EHI`, `attest_config`, `httpinjector/config`, `httpinjector/export_config`, `http-injector firebaseio` → **0 public hits**. (One 503 per-query is normal — retry.)

## 5. Where the hunt stands (working state)
- Host: `ehiapp.com` (only live pinned host; mycloudclient.com = dead nginx 404 on all `/httpinjector/*` GET+POST).
- Transport: cloud API returns AES-encrypted blob; `AES/CBC/NoPadding` + `CONFIG_AES_KEY`/`OLD_CONFIG_AES_KEY`/`IOS_CONFIG_AES_KEY` constants present in string pool but **key VALUES live in the DexHelper-encrypted dex — unreachable**. Same for the base host.
- To go further you need either: an APK predating 6.4 (unpacked), a rooted-device memory dump of the decrypted dex, or a MITM capture of a real in-app import (device with the app + a test key).
- Bot deliverable (@RasdAgent_bot, 5 engines + nm-vmess decode) is independent of this cloud-config API — cloud share-key decode stays "host unreachable" unless a capture arrives.
