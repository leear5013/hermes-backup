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
  --define:process.env.GAME_ENV='"prod"' --define:process.env.API_DOMAIN='""' \
  --define:'import.meta.env.MODE'='"production"' \
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
The deployed bundle's `loadJsonFromUrl` method **lacked** the `cache: "reload"`
patch that `loadBinaryFromUrl` had. This meant if the SW or HTTP cache had a
stale 404 for the manifest, the JSON loader would fail silently (no retry),
while the binary loader would recover. Manifest fetches are SMALL and CRITICAL
— they must always use the same cache-bypass + retry pattern as binary loads.

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