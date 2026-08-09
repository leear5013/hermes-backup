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

## mycloudclient.com / ehiapp.com — dead shells (2026-08-09)
These two domains came from the APK's `network_security_config.xml` and looked
promising:
- Both resolve (Cloudflare), but `mycloudclient.com` returns **404 on every
  path** (root, /api*, /config, /cloud, /getconfig, http and https).
- `ehiapp.com` root returns 200 with **0 bytes**; all paths 404.
- Wayback: only root/favicon/robots 301s, never a real site.
→ Not the (current) config backend. Do not re-probe.

## Next steps (when resumed)
1. **Strings-scan the current APK** for the cloud fetch URL. Latest versions on
   APKMirror: 6.5.0 (current), 6.4.0, 6.3.6, ... (path
   `apkmirror.com/apk/evozi/http-injector/`; version URLs match
   `http-injector-<ver>-release/`). Softpedia hosts a direct 5.6.4 APK
   (`mobile.softpedia.com/apk/http-injector/5.6.4/`); apkpure.net/br has 6.3.6.
   Extract `classes.dex` + `resources.arsc` via python zipfile, strings-scan
   for `config.ehi.link`, `ehi.link`, `getconfig`, `cloud`, `https://`.
   (VPS has no jadx/apktool — see references/apk-hunting.md.)
   **APK download chain is solved (2026-08-09):** APKMirror release page →
   `...-android-apk-download/` variant → `.../download/?key=<40-hex>` → APK
   bytes; full step-by-step in references/apk-hunting.md §0. The 6.5.0 fetch
   had reached the keyed URL when the sandbox reset; resume from there.
2. Check `app.ehi.link` (the importEvoziConfig intent target) for a web view or
   redirect that reveals the fetch pattern.
3. Once .ehi bytes are fetched, decrypt with HTTPINJECTOR.py engine
   (AES-CBC→AES-128→XXTEA, see SKILL.md).

## Pitfalls
- `config.ehi.link/<KEY>` page is identical for EVERY key — the key is read
  from `pathname` client-side. A 200 here proves nothing about key validity.
- The Next.js ehi.link wrapper's "invalid-link" message is client-side; the raw
  fetch layer is server-side / app-side.
- `cloud.httpinjector.com`, `mycloudclient.com`, `ehiapp.com` are all dead —
  don't re-probe them.
- When deobfuscating obfuscator.io JS: run it in node with mocked
  `document`/`window`/`navigator` rather than porting the decoder — the
  rotation loop (`0x815a8` checksum) is deterministic but pointless to
  re-implement. Instrument `window.location` with property getters to discover
  which URL field the script reads (pathname in this case).
