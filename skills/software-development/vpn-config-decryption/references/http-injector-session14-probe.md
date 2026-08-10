# HTTP Injector cloud-config — Session 14 (2026-08-10) — 6.3.6 packed, 5.7.0 no cloud feature, mirror verified

## Outcome in one line
Two more APKs scanned: **6.3.6 is DexProtector-PACKED** (packing predates 6.4 — earlier assumption wrong), and **5.7.0 has a real 10.6MB dex but ZERO cloud-feature strings** (the share-key feature is NOT in 5.7.0). The searchable window for a real-dex cloud-era build shrinks to **5.8.1–6.3.5** — IF any of those versions ship unpacked. androidapks.com verified as a working direct-download mirror (no JS gate).

## Downloads + scans (both via androidapks.com direct links, plain curl)

### 6.3.6 (`ehi636.apk`, 54.9 MB)
- **Packer: DexProtector, NOT DexHelper.** libs present: `libdexprotector.so`, `libdexprotector_h.so`, `libdpboot.so`, `libol.so`, `libevozi.so`, `libevozi_sentinel.so` — and **NO `libdatajar.so`** (that .so with the `/httpinjector/*` string pool exists only in 6.4.1/6.5.0).
- classes.dex 1.7MB (packed stub — compare 5.7.0's 6.3MB real dex), 8 dex files total (14.5MB combined incl. ads dex).
- **Zero hits** across all combined dex AND all 30 arm64 `.so` files for: `CONFIG_AES_KEY`, `OLD_CONFIG_AES_KEY`, `IOS_CONFIG_AES_KEY`, `configAesKey`, `configData`, `configSalt`, `Evozi-EHI`, `ehiapp`, `ehi.link`, `httpinjector`, `EncryptedApi`, `attest_config`, `CLOUD_SAVE`.
- Only generic `KEY`/`key=` strings in `libst.so` (OpenSSL), `libdf.so` (DNS forwarder), `libtunnelcore.so` (50MB — xray/v2ray core: `grpc-go`, `public_key=`, QUIC alpn strings) — all unrelated.
- **Packer-timeline correction:** DexProtector packing predates 6.4.1 (6.3.6 has it). The "packing started at 6.4" assumption is wrong; check for `libdexprotector*.so`/`libdpboot.so` too, not just DexHelper markers.

### 5.7.0 (`ehi570.apk`, 18.3 MB)
- **REAL dex**: classes.dex 6.3MB + classes2.dex 842KB (10.6MB total) — fully readable, no packer libs.
- **ZERO cloud-feature strings**: no `CONFIG_AES_KEY`, no `httpinjector`, no `cloud`, no `ehi.link`, no `Evozi-EHI`, no `configAesKey`/`configData`/`configSalt`. Only Google/ads URLs.
- → The share-key cloud feature (and its AES blob layer) appeared in **5.8.1–6.3.x**, not 5.7.0.

## Implication for the hunt
- Real-dex window to search for the `CONFIG_AES_KEY` VALUE: **5.8.1 → 6.3.5**, and only versions that ship unpacked. 6.3.6 already packed; 6.4+ DexHelper-packed (libdatajar.so string table gives API paths but never the key value).
- Scan order next session: 6.3.5, 6.3.4, 6.3.3, 6.3.2, 6.3.1, 6.3.0, 6.2.1, 6.2.0, 6.1.1, 6.0.0, 5.8.1 (androidapks.com has all of these). For each: check classes.dex size first (≥4MB = real, ~1-2MB = packed stub), check for `libdexprotector`/`libdpboot`/`DexHelper`/`###ACFNAME###`, then scan real dexes with `scripts/scan-dex-strings.py`.

## androidapks.com — VERIFIED working direct mirror (no JS gate)
- Old-versions page: `https://androidapks.com/http-injector/com-evozi-injector/old/` (plain urllib/curl fetch, no special UA needed).
- Each version's direct APK link is a signed `https://dl.androidapksfree.net/file/<20-hex>?e=<expiry-epoch>&s=<40-hex>` URL. **The version→link mapping trick: regex `6\.\d\.\d` and grab the nearest `dl.androidapksfree.net` link within ±300 chars in the HTML** (the link sits right after the version's own block).
- Downloads work with plain `curl -sL -o out.apk "<url>"`; verify `PK\x03\x04` magic after. No Cloudflare JS gate (unlike apkpure 403 and APKMirror JS-gated /download/?key= links).
- Old versions listed include 4.4.2 up to 6.3.6 (30+ versions) — this is the best mirror for this app.
