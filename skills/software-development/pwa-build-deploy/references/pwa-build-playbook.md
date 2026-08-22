# PWA Build Playbook — commands & worked example

Everything below was executed for real (OpenFront → FrontWar, deployed to
https://leear5013.github.io/frontwar/, 2026-08-21). Copy with modifications.

## 1. Upstream detection (is X a fork of open-source Y?)
```bash
curl -sL <site> -A "Mozilla/5.0" | grep -oE 'src="[^"]*\.js[^"]*"'   # bundle URLs
curl -sL <bundle-url> -o /tmp/bundle.js
python3 - <<'EOF'
of = open('/tmp/of.js').read(); fw = open('/tmp/fw.js').read()
for m in ['MIRVWarhead','defendedBorderColors','gameConfig']:      # signature strings
    print(m, 'OF=', m in of, 'FW=', m in fw)
EOF
```
Also compare route literals (`/auth/*`, `/users/@me`), Turnstile counts,
`dummy-admin-token` defaults. Check `api.github.com/repos/<upstream>` for
license (AGPL ⇒ must keep license + attribution in the fork).

## 2. Node 22 on this box (vite needs fs.globSync)
```bash
cd /opt/work && curl -sLO https://nodejs.org/dist/v22.14.0/node-v22.14.0-linux-x64.tar.xz
apt-get install -y xz-utils && tar -xf node-v22.14.0-linux-x64.tar.xz
export PATH=/opt/work/node-v22.14.0-linux-x64/bin:$PATH
```

## 3. Build client with esbuild (vite/rollup OOMs: exit 137, cgroup ~1GB)
Do NOT iterate `-Xmx` / `--minify false` — four attempts all died in transform.
esbuild does the same job in <1s:
```bash
npx esbuild src/client/Main.ts --bundle --outfile=<pwa>/src/of_client.js \
  --format=esm --platform=browser --jsx=automatic \
  --loader:.ts=ts --loader:.tsx=tsx \
  --loader:.glsl=text --loader:.vert=text --loader:.frag=text \
  --loader:.css=css --loader:.png=dataurl --loader:.svg=dataurl \
  --loader:.woff2=file --loader:.woff=file --loader:.mp3=file --loader:.json=json \
  --external:tailwindcss \
  --define:process.env.GAME_ENV='\"prod\"' --define:process.env.API_DOMAIN='\"\"' \
  --define:'import.meta.env.MODE'='\"production\"' \
  --define:'import.meta.env.PROD'=true --define:'import.meta.env.DEV'=false \
  --log-limit=0
```
Notes: `.glsl?raw` imports need the text loaders; tailwindcss import errors if
aliased (alias points at package.json) — use `--external:tailwindcss` and
compile CSS separately; CSS is emitted as a sibling `<outname>.css`.

## 4. Tailwind v4 (CSS-first) — REQUIRED or app ships unstyled
Find the entry (`grep -rn '@import "tailwindcss"' src/`) then:
```bash
npx @tailwindcss/cli -i src/client/styles.css -o <pwa>/src/of_client.css \
  --content "src/**/*.{ts,tsx},index.html"     # ~240KB real output vs 15KB stub
```
Sanity-check utilities exist: `grep -c 'lg\\:hidden' out.css`.
AND link it in index.html — esbuild/vite-cli do not inject the tag:
```html
<link rel="stylesheet" href="./src/of_client.css" />
```
Symptom if skipped: duplicated navs, broken panels, "?" icon placeholders,
~30KB screenshot instead of ~100KB.

## 5. Game worker (vite ?worker&inline breaks under esbuild)
Runtime error later: "GameWorker is not a constructor" at game start.
```bash
npx esbuild src/core/worker/Worker.worker.ts --bundle \
  --outfile=<pwa>/src/game-worker.js --format=iife --platform=browser \
  <same loaders + defines> --define:__ASSET_MANIFEST__='{}'
```
Patch client bundle (minified form varies; locate via `?worker&inline` marker):
```js
// replace: const {default:GameWorker}=await Promise.resolve().then(()=>(...));
//          return new GameWorker();
return new Worker("./src/game-worker.js");   // RELATIVE path for Pages subpath
```

## 6. Shell globals the client expects
Vite normally injects these via `define`/template. In hand-written index.html:
```html
<script>
  window.__ASSET_MANIFEST__ = {};
  window.BOOTSTRAP_CONFIG = { gitCommit:"pwa", assetManifest:{}, cdnBase:"",
    gameEnv:"prod", numWorkers:2, turnstileSiteKey:null, jwtAudience:null };
</script>
```
Missing manifest global fails only when a game starts ("error creating client
game ReferenceError") — test the full flow.

## 7. iOS/PWA shell checklist
- viewport: `width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no, viewport-fit=cover`
- `apple-mobile-web-app-capable`, `apple-mobile-web-app-status-bar-style=black-translucent`, `apple-touch-icon` 180×180 (PIL: flatten RGBA onto bg, LANCZOS resize)
- body padding `env(safe-area-inset-*)`; double-tap zoom block via touchend listener `{passive:false}`
- manifest.json: `display:"standalone"`, icons any+maskable 512, start_url/id relative later
- sw.js: SHELL_CACHE precache list, cache-first w/ network fallback, MAP_CACHE for `/maps/`, never intercept `/api`|`/auth`

## 8. Local headless verification (before deploy)
```python
# PLAYWRIGHT_BROWSERS_PATH=/opt/work/.pw-browsers; chromium launch args for GL:
args=['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']
pg.goto(url, wait_until='networkidle'); pg.wait_for_timeout(2500)
ok = pg.evaluate("()=>['play-page','desktop-nav-bar'].map(t=>!!customElements.get(t))")
```
Full-flow test: click menu → Solo → Start Game → assert page alive & no
pageerrors. Track 4xx via `page.on('response')`. Screenshot-size heuristic:
30KB = unstyled, 100KB = styled.
Subpath simulation: serve the PARENT dir, hit `/repo/` — NOT the repo dir as root.
GPU-less box limits: upstreams that check renderer string reject SwiftShader
(`GLUnavailableError ... software`); menu/logic still testable — don't debug.

## 9. GitHub Pages deploy (token in /data/.git-credentials, Bearer only)
```bash
TOKEN=$(grep -oE 'x-access-token:[^@]+' /data/.git-credentials | cut -d: -f2)
git init && git add -A && git -c user.name=... -c user.email=... commit -m v1
git branch -M main
git remote add origin https://x-access-token:${TOKEN}@github.com/<user>/<repo>.git
git push -q -u origin main
# create repo first: POST /user/repos {"name":"<repo>","private":false}
# enable pages:      POST /repos/<user>/<repo>/pages {"source":{"branch":"main","path":"/"}}
# poll: GET /repos/<user>/<repo>/pages/builds/latest -> status=="built"
```
Make ALL paths relative BEFORE pushing: index.html links/scripts, Worker() URL,
SW cache list, manifest start_url/id/scope/icon srcs (`./x`).

## 10. Production verification
Playwright against live URL: custom elements register, full solo flow runs,
manifest fetch 200, after one reload `navigator.serviceWorker.getRegistration()`
truthy. Brief CDN 404s right after build are propagation, not breakage — re-test.

## 11. Worker asset-manifest handshake (workers reset their globals)
The worker bundle's build-time `--define:__ASSET_MANIFEST__='{}'` OVERWRITES
globalThis at worker startup — the worker then builds absolute `/maps/...`
URLs that 404 under a subpath even though the main thread is fixed. Symptom:
"Failed to load ./maps/world/manifest.json" from the worker while the same URL
curl-checks 200. Fix — three small patches:
```js
// game-worker.js, right after the define assignment:
self.postMessage({ type: "worker-ready" });
self.addEventListener("message", (e) => {
  const d = e.data || {};
  if (d.type === "asset-manifest" && d.manifest && typeof d.manifest === "object")
    globalThis.__ASSET_MANIFEST__ = d.manifest;
});

// client bundle createGameWorker():
const w = new Worker("./src/game-worker.js");
w.addEventListener("message", function once(e) {
  if (e.data && e.data.type === "worker-ready") {
    w.postMessage({ type: "asset-manifest", manifest: getAssetManifest() });
    w.removeEventListener("message", once);
  }
});
return w;
```
Verify by logging every request URL matching `/maps/` in playwright — all must
start with `/frontwar/` (the subpath), none at domain root.

## 12. SW cache poisoning on installed devices (the bug that survives deploys)
Server fixes don't reach a phone whose service worker cached the 404s: iOS
HTTP-caches sw.js up to 10 min (GitHub Pages: max-age=600), and cache-first
SW rules serve stale garbage forever. The user hit the SAME error twice after
both fixes were verified live. Defense in depth (all four shipped):
```js
// sw.js
const VERSION = 'fw-v1.2.0';                 // bump EVERY deploy → old caches purged on activate
// JSON manifests: network-first so deploys always win
if (req.url.endsWith('.json') && req.url.includes('/maps/')) {
  event.respondWith(fetch(req).then(res => {
    if (res.ok) caches.open(MAP_CACHE).then(c => c.put(req, res.clone()));
    return res;
  }).catch(() => caches.open(MAP_CACHE).then(c => c.match(req))));
  return;
}
```
```js
// app loaders (main + worker): cache-bypass first attempt, plain retry, then give up loudly
let response;
try { response = await fetch(url, { cache: "reload" }); }
catch (e) { response = await fetch(url); }
if (!response.ok) { try { response = await fetch(url, { cache: "reload" }); } catch (e2) {} }
```
```js
// index.html one-time self-heal: deletes poisoned caches on next open
if (!localStorage.getItem("fw-healed-v1.2")) {
  localStorage.setItem("fw-healed-v1.2", "1");
  caches.keys().then(keys =>
    Promise.all(keys.filter(k => k.startsWith("fw-")).map(k => caches.delete(k)))
  ).then(() => location.reload());
}
```
User instruction that works: close PWA fully (app switcher), reopen, let it
self-reload once.

## 13. CRITICAL: loadJsonFromUrl MUST also use cache-bypass (discovered 2026-08-21)
The deployed bundle's `loadJsonFromUrl` method **lacked** the `cache: "reload"` patch that `loadBinaryFromUrl` had. This meant if the SW or HTTP cache had a stale 404 for the manifest, the JSON loader would fail silently (no retry), while the binary loader would recover. Manifest fetches are SMALL and CRITICAL — they must always use the same cache-bypass + retry pattern as binary loads.

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
This patch was missing from the deployed `frontwar2` bundle and caused the
user's fresh-device failure ("Failed to load ./maps/world/manifest.json" at
`loadJsonFromUrl` line 26994). After adding it, both loaders have identical
cache-bypass + retry logic.

## 14. CRITICAL: Asset manifest values MUST be ABSOLUTE URLs, not relative (discovered 2026-08-21)
The upstream's `buildAssetUrl()` falls back to `/${path}` for missing manifest entries, and even when present, relative values like `./maps/world/manifest.json` are used verbatim in fetches. Under a subpath (`/frontwar2/`) with SW caching, these can resolve incorrectly or produce confusing error messages (the error shows the relative path even though the server returns 200 for the absolute path).

The fix: when generating `BOOTSTRAP_CONFIG.assetManifest` in index.html, make every value an absolute URL via `new URL(relativePath, document.baseURI).href`. Do this for BOTH the main thread manifest AND the worker's postMessage manifest.

Result: fetches always hit `https://leear5013.github.io/frontwar2/maps/world/manifest.json` (200), error messages show full URLs, and no ambiguity in SW/browser resolution.

Regenerator script (`scripts/generate_asset_manifest.py`) updated to emit absolute URLs.

## 15. CRITICAL: Carrier/CDN caches can make ALL server-side fixes invisible — FRESH PATH is the nuclear option (discovered 2026-08-21)
GitHub Pages `max-age=600` + Egyptian carrier caches served users a weeks-old bundle even from "fresh browsers"; versioned query strings don't help because the cached HTML itself is what's stale. Fingerprint which bundle a remote user runs from their pasted error (`?v=` + line numbers) before debugging. If users still report old-code symptoms after one versioned redeploy, migrate to a FRESH PATH (new repo `/app2/`) — an uncached URL is the only guaranteed delivery. Worked: frontwar → frontwar2 migration fixed instantly what three correct fixes could not.

### Error fingerprinting technique
When a user pastes an error with a bundle hash (e.g., `of_client.js?v=38353c27f5:26994:17`), extract the hash and line number. Cross-reference against your deployed bundles — if it's an old hash, the user is running stale code regardless of what you deployed. Three correct fixes deployed to the same path failed to reach the user; a new repo (`frontwar2`) with fresh URLs delivered the fix on first try.

### When to use fresh path migration
- User reports same error after ≥1 correct deploy to same path
- User's error line numbers match an OLD bundle hash
- Carrier/CDN cache behavior is known to be aggressive (Egyptian ISP, corporate proxies)
- You've verified the fix is live but user still sees old behavior

## 16. Debugging checklist for "Failed to load ./maps/..." on PWA
1. **Fingerprint the bundle** — extract `?v=` hash from user's error; verify it matches your latest deploy
2. **Check manifest values** — are they absolute (`/app/maps/...`) or relative (`./maps/...`)? Must be absolute
3. **Check both loaders** — `loadJsonFromUrl` AND `loadBinaryFromUrl` need cache-bypass + retry
4. **Check worker handshake** — worker must receive absolute manifest via postMessage, not rely on its own build-time define
5. **Check SW rules** — JSON manifests must be network-first; bump SW version on every deploy
6. **If all above correct and user still fails** — migrate to fresh path (new repo/app2)
7. **Production smoke test** — playwright against LIVE URL (not localhost): manifest fetch 200, map.bin 200, zero 4xx, no "?" icons

## 17. CRITICAL: Prevent SW registration on game-specific paths (discovered 2026-08-21)
Upstream games with multiplayer use `ClientEnv.workerPath(gameID)` to build URLs like `/w1/game/<id>`. When the PWA navigates to such a URL (via `history.pushState`), the `load` event fires again. If the SW registration code runs unconditionally on every `load`, it tries to register `./sw.js` **relative to the game path** (e.g., `/w1/game/<id>/sw.js` → 404, and logs "[FW] SW registration failed: A bad HTTP response code (404)").

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

## References
- `scripts/generate_asset_manifest.py` — rebuilds BOOTSTRAP_CONFIG.assetManifest in index.html (run after adding any assets; see subpath pitfall above). Updated to emit absolute URLs.
- `scripts/pwa_smoke_test.js` — production smoke test: broken images, 4xx/5xx, undefined custom elements, page errors at mobile or desktop viewport. Run against the LIVE URL after every deploy (localhost passes hide this entire bug class). Requires playwright; browsers at PLAYWRIGHT_BROWSERS_PATH=/opt/work/.pw-browsers.
- Companion skill `pwa-static-hosting` carries the full incident case file (`references/frontwar-openfront-case.md`) — live URL, patch points, debugging recipes, and honest open-issue status.