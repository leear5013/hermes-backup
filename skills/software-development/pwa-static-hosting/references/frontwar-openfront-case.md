# Case File: FrontWar PWA (OpenFront fork) — 2026-08-21

Project for Hesham: rebrand OpenFront.io (AGPL, github.com/openfrontio/OpenFrontIO)
as "FrontWar" with iPhone-PWA + APK support.

**LIVE URL: `https://leear5013.github.io/frontwar2/`** (repo `leear5013/frontwar2`,
source of truth `/opt/work/frontwar2/`). The original
`https://leear5013.github.io/frontwar/` is ABANDONED — Egyptian carrier caches
served users stale bundles there no matter what was deployed; versioned query
strings were useless because the cached HTML itself never refreshed. Fresh-path
migration was the only thing that worked. Upstream clone: `/opt/work/openfront/`.

## State map
- Client bundle `src/of_client.js` (esbuild ESM, ~4.8MB), worker
  `src/game-worker.js` (esbuild IIFE). Both content-versioned via `?v=` in
  `index.html`.
- `index.html`: hand-built shell — iOS meta tags, safe-area CSS,
  `window.__ASSET_MANIFEST__ = {}`, `BOOTSTRAP_CONFIG` (gitCommit pwa-local,
  assetManifest = full disk-generated map to relative paths, gameEnv prod,
  jwtAudience localhost, instanceId fw-pwa-01, numWorkers 2).
- `sw.js` v1.3.0: precache shell+worker+atlases; maps network-first-for-JSON /
  cache-first-for-binaries; version-bumped cache purge; self-heal flag
  `fw-healed-v1.2`.
- Maps shipped: world, europe, asia, africa, australia, britannia, iceland,
  japan, northamerica, southamerica.

## Exact patch points in the bundle (re-apply after any rebuild)
1. `createGameWorker()` → replace dynamic import with
   `new Worker("./src/game-worker.js?v=<hash>")` plus a synchronous
   `postMessage({type:"asset-manifest", manifest:<absolute-URL entries>})`
   immediately after construction.
2. Worker `buildAssetUrl` → prefer absolute manifest entries before any baseUrl
   concatenation.
3. Worker accepts `{type:"asset-manifest"}` messages into
   `globalThis.__ASSET_MANIFEST__` (its build-time define is empty and it would
   otherwise overwrite anything set on globalThis).

## Debugging techniques that worked
- Stale-code fingerprinting: a user-pasted stack trace contains the bundle
  `?v=` and exact line numbers — diff against the deployed file to detect
  "user runs old JS" BEFORE debugging the reported symptom. Three rounds of
  correct server-side fixes were invisible because of this.
- Custom-element audit: runtime `customElements.get(tag)` over all tags parsed
  from index.html (grep of minified define calls finds nothing).
- Broken images: evaluate `img.complete && img.naturalWidth===0` live; sweep
  `page.on("response")` for 4xx — this found the entire subpath-404 class that
  on-disk file checks "passed".
- Main-vs-worker request attribution: Playwright `page.on("request")` sees
  worker fetches too; `r.frame is None` ⇒ worker context.
- Mobile-only repro: `p.devices["iPhone 13"]` emulation surfaced failures
  desktop runs never showed. Note its limits: JS `.click()` can hit detached
  nodes after lit re-renders (use locators + real taps for UI-behavior bugs;
  JS clicks are fine for network-flow bugs).
- Playwright browsers: use `/usr/local/bin/python3` with
  `PLAYWRIGHT_BROWSERS_PATH=/opt/work/.pw-browsers`; the /opt/venv playwright
  expects a different browser build number and fails.
- git push via token: if `src refspec main does not match any`, the local
  branch is still `master` (git default) — `git branch -M main` before push.

## CRITICAL FIX (2026-08-21): loadJsonFromUrl missing cache-bypass
The deployed `frontwar2` bundle's `loadJsonFromUrl` method lacked the
`cache: "reload"` patch that `loadBinaryFromUrl` had. This meant if the SW or
HTTP cache had a stale 404 for the manifest, the JSON loader would fail
silently (no retry), while the binary loader would recover. Manifest fetches
are SMALL and CRITICAL — they must always use the same cache-bypass + retry
pattern as binary loads.

The user reported the error on a **fresh device with the new URL** showing the
failure at `loadJsonFromUrl` line 26994 — this was the missing patch causing
the failure.

Patch to apply in the bundle (search for `async loadJsonFromUrl`):
```js
async loadJsonFromUrl(url2) {
  let response;
  try { response = await fetch(url2, { cache: "reload" }); }
  catch (e) { response = await fetch(url2); }
  if (!response.ok) {
    try { response = await fetch(url2, { cache: "reload" }); } catch (e2) {}
  }
  if (!response.ok) {
    throw new Error(`Failed to load ${url2}: ${response.statusText}`);
  }
  return response.json();
}
```

## OPEN ISSUES (unresolved — do not present as fixed)
- **Final map render on the user's device: unconfirmed.** After the fresh-path
  migration, the worker correctly fetched `/frontwar2/maps/world/manifest.json`
  (200, no retries, no errors — the manifest 404 class is RESOLVED). Whether
  the map actually renders on the user's iPhone is still unknown; if it shows
  black, suspect the WebGL layer (see below), not the manifest bug.
- **Suspected self-inflicted loader bug (not yet reverted):** the worker
  bundle carries a custom `cache:"reload"` + retry patch in its
  `loadJsonFromUrl`/`loadBinaryFromUrl` from the stale-cache era. During local
  mobile-emulation testing (pre-migration) the worker fetched the manifest 200
  six times then failed without ever requesting `map.bin`. If solo-start ever
  regresses on /frontwar2/, FIRST strip the custom loader patches from the
  worker (keep only the absolute-manifest handshake), re-version, redeploy.
- Multiplayer lobby/matchmaking needs the upstream Node game server
  (`ws…/w0|w1/lobbies` 404s on GitHub Pages by design); solo should not depend
  on it but the client still attempts the lobby socket. Cosmetic errors from
  `localhost:8787` (cosmetics/news/streams/auth) are the same class — set
  `jwtAudience: "localhost"` so they fail fast instead of DNS-hanging on
  `api.null`.
- Map rendering requires real-GPU WebGL2; upstream deliberately rejects
  SwiftShader/software GL, so headless servers can never render the final map
  (expected limitation, not a bug).

## Environment notes
- Node 22 tarball at `/opt/work/node-v22.14.0-linux-x64/bin` (fs.globSync in
  vite config needs ≥22).
- Local subpath test rig: symlink dir under a parent served by
  `python3 -m http.server` so `/frontwar2/` behaves like GitHub Pages.
- Subagent delegation: one QA agent wrote scratch files into /data and its
  disk-fill killed the whole parallel fleet mid-run. Always put "write ONLY to
  /tmp and /opt/work — never /data" in every delegate_task context block, and
  check `df -h /data` before dispatching heavy work.