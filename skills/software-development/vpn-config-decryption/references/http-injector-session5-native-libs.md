# HTTP Injector 6.5.0 — native-lib analysis (session 5, 2026-08-09)

Goal: find the base host / request builder for the `/httpinjector/*` cloud API.
Result: host NOT found statically — but the last remaining static lead is
located and characterized: the ehi-cloud JNI bridge has ciphered strings.

## libdatajar.so (~20MB, from config.arm64_v8a.apk split) — plaintext dex string pool

- All `/httpinjector/*` paths sit in ONE contiguous string block (a dex string
  pool) mixed with ad-SDK strings. Pool neighborhood order:
  `%s.properties`, `.//pagead2.googlesyndication.com/pagead/gen_204`, `/Download/`,
  `/HTTP Injector/`, `aclk`, `cmdline`, `/data/app/`, `/data/data/`,
  `/httpinjector/attest_config`, `/httpinjector/backup`, `/httpinjector/config`,
  `/httpinjector/export_config`, `/httpinjector/import_config`,
  `/httpinjector/login`, `/httpinjector/servers`, `/iap/verification`,
  `/pagead/adview`, `/pagead/conversion`, `/pcs/click`, `/pcs/view`.
- **NO base-URL literal anywhere in the 20MB.** Full URL-literal list is
  Google/AdMob/DNS-over-HTTPS/ads only: `goo.gle/*`, `pagead2.googlesyndication.com`,
  `dns.mullvad.net`, `cloudflare-dns.com`, `dns.google`, `dns.quad9.net`,
  `freedns.controld.com`, `dns-unfiltered.adguard.com`, `dns.alidns.com`,
  `doh.pub`, `doh.360.cn`, `adx.ads.vungle.com`, `config.ads.vungle.com`,
  `events.ads.vungle.com`, `logs.ads.vungle.com`, `www.facebook.com/adnw_logging/`,
  `play.google.com/store/apps/details?id=`, `plus.google.com`, `market://details?id=`.
  Notable non-Google: **`ss://%s:%s@%s:%s`** (share-link builder) and
  **`evozi:stun.syncthing.net:3478`** (STUN server, `evozi:` prefix = app-owned).
- HTTP-style word counts: GET 18, POST 8, PUT 9, DELETE 31, `OkHttp` 14, `okhttp` 29,
  `Content-Type` 2, `application/json` 1, `application/x-www-form-urlencoded` 1,
  `setRequestMethod` 1, `RequestBody` 39, `FormBody` 0, `URLConnection` 4 →
  OkHttp + JSON-style requests.
- String-pool read technique: `data.find(target)` then `repr(data[i-400:i+200])`;
  always write dumps to a file (terminal `| head` collapses to "1 lines output").

## libdexjniehi.so (~1.5MB) — the ehi-cloud JNI bridge — STRINGS ARE CIPHERED

- No URL literals, no plaintext ehi strings. All printable runs are
  substitution-ciphered. Samples (from `re.findall(rb'[\x20-\x7e]{3,}', data)`):
  - `nere+hejc+Glevegpav`
  - `nere+hejc+MhhacehWpepaA|gatpmkj`
  - `nere+hejc+MhhacehEggawwA|gatpmkj`
  - `nere+hejc+Mjpavvqtpa`A|gatpmkj`
  - `nere+hejc+Wlkvp`, `nere+hejc+@kqfha`, `nere+hejc+F}pa`
  - `nere+hejc+Kfnagp?` (with many single-letter suffixes: `-R -M -W -G -F -N -^ -B -@` — looks like a per-char key or lookup table)
  - `nere+hejc+MjpavjehAvvkv`, `nere+hejc+MhhacehEggawwAvvkv`
  - `nere+mk+MKA|gatpmkj`, `nere+hejc+KqpKbIaikv}Avvkv`
- `nere+hejc` repeated prefix = likely a class-name/package prefix (the `+` is
  probably a separator, e.g. `Xxx+yyy` from a `$`/`.`). Cipher NOT cracked yet.
  Repeated ciphertext fragments (`Mhhaceh`, `gatpmkj`, `WpepaA`) = repeated
  plaintext substrings (method suffixes like `Config`, `UrlBuilder`).
- **This lib is the last static lead** — it is the JNI bridge that would build
  the base URL at runtime. A Caesar/substitution crack (or frequency analysis,
  the repeated `gatpmkj` suffix is a strong crib) should reveal the host and
  request builder.

## ehiapp.com apex — 405/404 behavior characterized (don't re-permute blindly)

- GET+POST on `/httpinjector/*` → 405 EMPTY body (route exists, verb/param shape
  unknown); `/httpinjector/login` + `/iap/verification` → 404 JSON
  `{"error":"Not found"}` (real JSON backend behind Cloudflare).
- PUT/OPTIONS/PATCH on any path → Cloudflare 301 → www.ehiapp.com → 403 WAF page.
  Raw HTTP/1.0 probe gives the same 301. **Never follow the apex 301.**
- Content-Type permutations (json / x-www-form-urlencoded / text/plain /
  octet-stream) and query-param shapes (key=, config_key=, code=, id=, k=) all →
  405. Don't re-run these without the actual request builder from the cipher or
  runtime interception (mitmproxy on a real device).
- `ehi.tips` / `www.ehi.tips` (from resources.arsc) → NXDOMAIN — dead, don't re-probe.
- `crt.sh` subdomain enumeration returned 502 Bad Gateway this session (Cloudflare
  rate-limit) — retry with a delay if needed; subdomains of ehiapp.com /
  mycloudclient.com were NOT enumerated.

## Extraction recipe (no unzip binary on VPS)

```python
import zipfile
z = zipfile.ZipFile('config.arm64_v8a.apk')
for n in ['lib/arm64-v8a/libdatajar.so', 'lib/arm64-v8a/libdexjniehi.so']:
    open(n.split('/')[-1], 'wb').write(z.read(n))
```
