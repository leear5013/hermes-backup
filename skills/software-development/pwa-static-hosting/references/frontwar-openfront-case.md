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
  assetManifest = full disk-generated map to **absolute URLs**, gameEnv prod,
  jwtAudience localhost, instanceId fw-pwa-01, numWorkers 2).
- `sw.js` v2.0.0: precache shell+worker+atlases; maps network-first-for-JSON /
  cache-first-for-binaries; version-bumped cache purge; self-heal flag
  `fw-healed-v2.0`.
- Maps shipped: world, europe, asia, africa, australia, britannia, iceland,
  japan, northamerica, southamerica.

## Exact patch points in the bundle (re-apply after any rebuild)
1. `createGameWorker()` → replace dynamic import with
   `new Worker("./src/game-worker.js?v=<hash>")` plus include the **absolute
   asset manifest in the `init` message** (not a separate postMessage after
   `worker-ready` — the game can start before the handshake completes). The
   `init` payload must carry `assetManifest: <absolute-URL entries>`.
2. Worker `buildAssetUrl` → prefer absolute manifest entries before any baseUrl
   concatenation.
3. Worker `init` handler → on `message.assetManifest`, set
   `globalThis.__ASSET_MANIFEST__ = message.assetManifest` before creating the
   `FetchGameMapLoader` (which captures the manifest at construction time).
4. `loadJsonFromUrl` in `FetchGameMapLoader` (both main thread and worker) →
   add `cache: "reload"` first attempt + plain retry + second `cache: "reload"`
   retry before throwing. This patch was MISSING from the deployed bundle and
   caused the user's fresh-device failure ("Failed to load ./maps/world/manifest.json"
   at `loadJsonFromUrl` line 26994). Now applied and verified.

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

## CRITICAL FIX (2026-08-21): Asset manifest values MUST be ABSOLUTE URLs
The upstream's `buildAssetUrl()` falls back to `/${path}` for missing manifest
entries, and even when present, relative values like `./maps/world/manifest.json`
are used verbatim in fetches. Under a subpath (`/frontwar2/`) with SW caching,
these can resolve incorrectly or produce confusing error messages (the error
shows the relative path even though the server returns 200 for the absolute path).

The fix: when generating `BOOTSTRAP_CONFIG.assetManifest` in index.html, make
every value an absolute URL via `new URL(relativePath, document.baseURI).href`.
Do this for BOTH the main thread manifest AND the worker's postMessage manifest.

Result: fetches always hit `https://leear5013.github.io/frontwar2/maps/world/manifest.json`
(200), error messages show full URLs, and no ambiguity in SW/browser resolution.

Regenerator script (`scripts/generate_asset_manifest.py`) updated to emit absolute URLs.

## CRITICAL FIX (2026-08-21): Carrier/CDN caches can make ALL server-side fixes invisible — FRESH PATH is the nuclear option
GitHub Pages `max-age=600` + Egyptian carrier caches served users a weeks-old bundle even from "fresh browsers"; versioned query strings don't help because the cached HTML itself is what's stale. Fingerprint which bundle a remote user runs from their pasted error (`?v=` + line numbers) before debugging. If users still report old-code symptoms after one versioned redeploy, migrate to a FRESH PATH (new repo `/app2/`) — an uncached URL is the only guaranteed delivery. Worked: frontwar → frontwar2 migration fixed instantly what three correct fixes could not.

### Error fingerprinting technique
When a user pastes an error with a bundle hash (e.g., `of_client.js?v=38353c27f5:26994:17`), extract the hash and line number. Cross-reference against your deployed bundles — if it's an old hash, the user is running stale code regardless of what you deployed. Three correct fixes deployed to the same path failed to reach the user; a new repo (`frontwar2`) with fresh URLs delivered the fix on first try.

### When to use fresh path migration
- User reports same error after ≥1 correct deploy to same path
- User's error line numbers match an OLD bundle hash
- Carrier/CDN cache behavior is known to be aggressive (Egyptian ISP, corporate proxies)
- You've verified the fix is live but user still sees old behavior

## CRITICAL FIX (2026-08-21): SW registration path MUST be absolute with explicit scope
`navigator.serviceWorker.register("./sw.js")` is relative. When the singleplayer URL rewrite changes the page to `/wX/game/...`, a subsequent load event fires and the SW registers from THAT path, resolving to `/wX/game/sw.js` (404). Fix: use absolute path + explicit scope:
```js
navigator.serviceWorker.register("/frontwar2/sw.js?v=14",
  { scope: "/frontwar2/" })
```
This ensures the SW always registers at the correct subpath regardless of current page URL.

## CRITICAL FIX (2026-08-21): Prevent SW registration on game-specific paths (discovered 2026-08-21)
Upstream games with multiplayer use `ClientEnv.workerPath(gameID)` to build URLs like `/w1/game/<id>`. When the PWA navigates to such a URL (via `history.pushState`), the `load` event fires again. If the SW registration code runs unconditionally on every `load`, it tries to register `./sw.js` **relative to the game path** (e.g., `/w1/game/<id>/sw.js` → 404, and logs `"[FW] SW registration failed: A bad HTTP response code (404)"`).

**Fix:** In index.html, make SW registration **path-aware**:
```js
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    // Only register on the ROOT path — game URLs (/w1/game/*, /game/*) are not
    // PWA scope and should not re-register the SW.
    const isGamePath = window.location.pathname.startsWith("/w") ||
                       window.location.pathname.startsWith("/game");
    if (!isGamePath) {
      navigator.serviceWorker.register("/frontwar2/sw.js?v=14").then(...);
    }
  });
}
```
Key points:
- Use **absolute SW URL** (`/frontwar2/sw.js`) not relative — survives any URL pushState
- Gate on pathname: only register at the app root (`/` or `/frontwar2/`)
- Bump SW version (`v=14`) on every deploy so old caches purge
- The game's LocalServer flow (solo) does NOT need a game-specific SW scope

## CRITICAL FIX (2026-08-21): Singleplayer games MUST NOT update the URL via `workerPath`
There are AT LEAST TWO places in the codebase that rewrite the browser URL for singleplayer games:

### Point 1: `updateJoinUrlForShare` in `handleJoinLobby` (Main.ts)
This was the initially discovered path. Fix:
```ts
if (lobby.source !== "public" && lobby.source !== "singleplayer") {
  this.updateJoinUrlForShare(lobby.gameID);
}
```

### Point 2: `lobbyHandle.join.then(...)` callback — THE PRIMARY CULPRIT
This fires when the lobby join promise resolves and pushes state via:
```ts
history.pushState(null, "", `/${ClientEnv.workerPath(lobby.gameID)}/game/${lobby.gameID}?live`);
```
This is the code that actually navigates the browser to `/w1/game/<id>?live` on GitHub Pages, causing a 404. The `lobby` variable is available from the enclosing scope of the `joinLobby` call. Fix: guard the pushState:
```ts
this.lobbyHandle.join.then(() => {
  // ... other setup ...
  if (lobby.source !== "singleplayer") {
    history.pushState(null, "", `/${ClientEnv.workerPath(lobby.gameID)}/game/${lobby.gameID}?live`);
  }
  this.currentUrl = window.location.href;
});
```

**Diagnosis pattern:** When user reports "game is loading" hang OR "Connection error" with URL like `/w1/game/xxx?live` on GitHub Pages, the URL changed via `lobbyHandle.join.then(...)`, NOT `updateJoinUrlForShare`. Search the deployed bundle for ALL `workerPath` + `pushState` combinations — there are 13+ references.

## Debugging checklist for "Failed to load ./maps/..." on PWA
1. **Fingerprint the bundle** — extract `?v=` hash from user's error; verify it matches your latest deploy
2. **Check manifest values** — are they absolute (`/app/maps/...`) or relative (`./maps/...`)? Must be absolute
3. **Check both loaders** — `loadJsonFromUrl` AND `loadBinaryFromUrl` need cache-bypass + retry
4. **Check worker handshake** — worker must receive absolute manifest via init message, not rely on its own build-time define
5. **Check SW rules** — JSON manifests must be network-first; bump SW version on every deploy
6. **If all above correct and user still fails** — migrate to fresh path (new repo/app2)
7. **Production smoke test** — playwright against LIVE URL (not localhost): manifest fetch 200, map.bin 200, zero 4xx, no "?" icons

## RESOLVED ISSUES (as of 2026-08-21)
- **Worker manifest 404 class: RESOLVED via fresh-path migration + absolute manifest + loadJsonFromUrl patch.**
  The worker now correctly fetches `/frontwar2/maps/world/manifest.json` (200,
  no retries, no errors — verified in production Playwright run against live URL).
- **Subpath 404 for all assets: RESOLVED** — full assetManifest with absolute URLs
  generated and deployed.
- **SW cache poisoning on installed devices: MITIGATED** — SW v2.0.0, network-first
  for JSON manifests, self-heal flag, cache-bypass in loaders, versioned bundles.
  Fresh-path migration (`/frontwar2/`) is the ultimate escape from stale device caches.
- **Missing Tailwind CSS + duplicated navs: RESOLVED** — compiled via CLI and linked.

## OPEN ISSUES (unresolved — do not present as fixed)
- **Final map render on the user's device: unconfirmed.** After the fresh-path
  migration, the worker correctly fetched the manifest (200, no retries, no errors
  — the manifest 404 class is RESOLVED). Whether the map actually renders on the
  user's iPhone is still unknown; if it shows black, suspect the WebGL layer
  (see below), not the manifest bug.
- **Suspected self-inflicted loader bug (not yet reverted):** the worker
  bundle carries a custom `cache:"reload"` + retry patch in its
  `loadJsonFromUrl`/`loadBinaryFromUrl` from the stale-cache era. During local
  mobile-emulation testing (pre-migration) the worker fetched the manifest 200
  six times then failed without ever requesting `map.bin`. If solo-start ever
  regresses on /frontwar2/, FIRST strip the custom loader patches from the
  worker (keep only the absolute-manifest handshake), re-version, redeploy.
- Multiplayer lobby/matchmaking needs the upstream Node game server
  (`ws.../w0|w1/lobbies` 404s on GitHub Pages by design); solo should not depend
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