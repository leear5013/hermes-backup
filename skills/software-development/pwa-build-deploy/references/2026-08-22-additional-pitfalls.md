# Additional Pitfalls Discovered (2026-08-22)

## Singleplayer URL Navigation Fix (MULTIPLE POINTS — all must be patched)
There are AT LEAST THREE places in the codebase that rewrite the browser URL to `/w1/game/<id>?live` for singleplayer games, causing 404 on GitHub Pages and hanging the game. ALL must be patched:

### Point 1: `updateJoinUrlForShare` in `handleJoinLobby` (Main.ts)
Called for all non-public lobbies. Fix:
```ts
if (lobby.source !== "public" && lobby.source !== "singleplayer") {
  this.updateJoinUrlForShare(lobby.gameID);
}
```

### Point 2: `lobbyHandle.join.then(...)` callback (Main.ts, inside `joinLobby`)
This fires when the lobby join promise resolves and pushes state via `history.pushState(null, "", '/${ClientEnv.workerPath(lobby.gameID)}/game/${lobby.gameID}?live')`. This is the PRIMARY cause of the 404 navigation on GitHub Pages. The callback does NOT receive `lobby.source` — the `lobby` variable must be checked from the enclosing scope, or the entire pushState block must be guarded. Fix: skip the `history.pushState` for singleplayer by checking the lobby source before the push:
```ts
this.lobbyHandle.join.then(() => {
  // ... other setup ...
  // ONLY push URL state for multiplayer games
  if (lobby.source !== "singleplayer") {
    history.pushState(null, "", `/${ClientEnv.workerPath(lobby.gameID)}/game/${lobby.gameID}?live`);
  }
  this.currentUrl = window.location.href;
});
```

### Point 3: `viewGame()` methods in profile/game-listing components
These call `history.pushState({ join: gameId }, "", newUrl)` when viewing a game from the lobby list. These are NOT triggered for singleplayer games (they're user-initiated view actions), so they don't need patching — but be aware they exist if debugging URL issues.

**Diagnosis tip:** When the user reports "game is loading" hang OR "Connection error" with a URL like `/w1/game/xxx?live` on GitHub Pages, the URL change happened BEFORE the game initialized. Search the deployed bundle for ALL `workerPath` + `pushState` combinations — there are 13+ references, not just one.

## CRITICAL: Service Worker Cache-First Serves Stale Worker Bundle
The SW "Everything else" fallback handler caches all non-map, non-navigation requests with **cache-first** strategy. This includes `game-worker.js` and `of_client.js`. After deploying a FIXED worker bundle:

1. The stale cached SW (old version) serves the OLD cached `game-worker.js`
2. The old worker lacks the `assetManifest` init-message handler
3. The worker sets `globalThis.__ASSET_MANIFEST__ = {}` (empty default) at startup
4. `buildAssetUrl()` in the worker falls back to `/maps/...` (root path) → **404 forever**
5. Map loader hangs → `"Worker initialization timeout"` (60s) → "Connection error"

**Symptoms:** Worker initialization timeout with NO map loader logs, even though curl of the manifest returns 200. Local tests pass (fresh SW), remote users fail (stale SW cache).

**Fix to SW fetch handler** — JS bundles must be network-first:
```js
// Add BEFORE the "Everything else" cache-first handler:
if (req.url.endsWith('.js')) {
  event.respondWith(
    fetch(req).then((res) => {
      if (res.ok) caches.open(ASSET_CACHE).then((c) => c.put(req, res.clone()));
      return res;
    }).catch(() => caches.open(ASSET_CACHE).then((c) => c.match(req)))
  );
  return;
}
```
Also bump SW `VERSION` (e.g. `fw-v2.0.0` → `fw-v2.1.0`) + registration `?v=<hash>` bump to force SW update on client devices.

## CRITICAL: Worker Manifest Race — Must Send via Init Message
The `worker-ready` → `asset-manifest` postMessage handshake is RACY: the `init` message (containing `gameStartInfo`) is sent immediately after Worker creation, but the worker's module-level code may not have attached its message listener yet. If the init fires before the listener is attached, the manifest is silently lost.

**Correct fix:** Include `assetManifest` **directly in the `init` message payload**, not as a separate postMessage. The worker's `init` handler sets `globalThis.__ASSET_MANIFEST__` from the message BEFORE calling `createGameRunner()`. This eliminates the race because the init message is queued and delivered after the worker's message listener is attached (the worker's `addEventListener("message")` is at module scope, runs synchronously).

## esbuild Does NOT Polyfill `process.env`
Vite injects `process.env.NODE_ENV` at build time. esbuild only does it for `--define` values you pass explicitly. Any code reading `process.env.X` at runtime throws `ReferenceError: process is not defined` — this affected `getApiBase()` → auth/cosmetics/news API calls, causing them to fail.

**Fix:** Add `--define:process.env.NODE_ENV='\"production\"'` and audit the bundle for remaining `process.env.*` reads. Post-bundle patch: `client.replace(/process\.env\.API_DOMAIN/g, 'void 0')` + `re.sub(r'process\.env\.NODE_ENV', '"production"', client)` — also catch `process.env.*` in regex comments to avoid `ReferenceError` from `.test()` on undefined.

## Turnstile Dependency in Solo Flow (OPEN — workaround patchable)
OpenFront's `Main.ts:1282` `getTurnstileToken()` awaits `window.turnstile` for 10s then throws. PWA has no Turnstile → promise rejects → `handleJoinLobby` catches → Transport falls back to lobby WS → connection fails → game hangs on "game is loading" before MapLoader runs.

**Workaround in bundle patch:** Replace the `while`/`throw` body of `getTurnstileToken` so it resolves immediately with a mock token when `!window.turnstile`, **but only after** the 10s poll fails to populate:
```js
if (typeof window.turnstile === "undefined") {
  return { token: "pwa-local-token", createdAt: Date.now() };
}
```
This lets `userAuth()` proceed, `isLocal()` returns true for Singleplayer, and the LocalServer starts.

## CRITICAL: `loadJsonFromUrl` Cache-Bypass Gap (2026-08-22)
The deployed bundle's `loadJsonFromUrl` **lacked** the `cache: "reload"` patch that `loadBinaryFromUrl` had. Manifests are SMALL and CRITICAL — they must always use cache-bypass + retry:
```js
async loadJsonFromUrl(url2) {
  const response = await fetch(url2, {cache: "reload"});
  if (!response.ok) {
    const retry = await fetch(url2, {cache: "reload"});
    if (!retry.ok) throw new Error(`Failed to load ${url2}: ${retry.statusText}`);
    return retry.json();
  }
  return response.json();
}
```

## CRITICAL: `new GameWorker()` / Worker Constructor Race
Under esbuild, Vite's `?worker&inline` (Blob worker pattern) breaks with `"GameWorker is not a constructor"`. Build the worker as a separate `.js` bundle and load via:
```js
async function createGameWorker() {
  const workerUrl = new URL('./game-worker.js?v=<hash>', import.meta.url).href;
  return new Worker(workerUrl);
}
```
The `<hash>` MUST match the deployed worker file name.

## Worker Timeout = "Worker initialization timeout"
The 60s timeout in `WorkerClient.initialize()` fires when the worker never sends `initialized`. Root causes:
- Worker file never loads (404 from SW stale cache)
- Worker script throws before posting `initialized` (manifest not set → assetUrl fails → map load throws)
- Worker init message handler missing `assetManifest` (empty manifest → absolute URLs fail)