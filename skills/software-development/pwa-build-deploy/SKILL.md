---
name: pwa-build-deploy
description: Use when forking a browser game/app into an installable PWA.
---

# PWA Build & Deploy (from open-source web apps/games)

Use when the user wants their own version of an existing open-source browser
game or web app — installable on iPhone (Add to Home Screen), wrappable as an
APK, hosted free with HTTPS. Worked example: OpenFront.io fork → "FrontWar"
PWA → live on GitHub Pages (2026-08-21). Also applies to any SPA/game with a
vite/esbuild toolchain.

## Core insight
Never rebuild from scratch. Find the open-source upstream (check client bundle
for shared signature strings vs a GitHub repo), fork it, rebrand, and re-host.
AGPL upstreams require license + attribution — keep both.

## Workflow

1. **Acquire upstream**: `git clone --depth 1 <repo>` into `/opt/work/`
   (never /data). Read `package.json` scripts + `vite.config.ts` first.
2. **Build the client — use esbuild, NOT vite/rollup on this box.**
   The 1GB cgroup OOM-kills `vite build` in the transform phase every time
   (exit 137, even at -Xmx 650–950MB, even `--minify false`). esbuild bundles
   the same entry in ~300ms. Exact command bank in references.
   - Needs Node ≥22 for `fs.globSync` (vite configs use it); system Node is 20.
     Install to /opt/work: nodejs.org tarball + `apt-get install xz-utils`.
3. **Bundle the worker separately.** Vite `?worker&inline` imports break under
   esbuild ("GameWorker is not a constructor"). Build the worker with
   `--format=iife`, then patch the client bundle's `createGameWorker()` to
   `return new Worker("./src/game-worker.js")`.
4. **Assemble the PWA shell** (hand-written index.html from upstream's):
   - `<link rel="stylesheet" href="./src/<bundle>.css">` — **esbuild does NOT
     inject stylesheets the way vite does; a missing link tag = fully unstyled
     app with duplicated navs. The user WILL notice and send a screenshot.**
   - Compile Tailwind v4 via CLI (`npx @tailwindcss/cli -i <entry.css> -o out
     --content "src/**/*.ts*"`) — `--external:tailwindcss` in esbuild ships NO
     utilities at all. Tailwind v4 is CSS-first: entry has `@import "tailwindcss"`.
   - Globals the client may expect that vite normally `define`s:
     `window.__ASSET_MANIFEST__ = {}` (and BOOTSTRAP_CONFIG if upstream uses one).
   - iOS: `apple-mobile-web-app-capable`, `black-translucent`, 180×180
     `apple-touch-icon`, `viewport-fit=cover` + safe-area insets, double-tap
     zoom block. `manifest.json` with `display: standalone`.
   - `sw.js`: cache-first shell + maps; never cache `/api` or `/auth`.
5. **Verify headless BEFORE deploying** (playwright, chromium at
   `PLAYWRIGHT_BROWSERS_PATH=/opt/work/.pw-browsers`):
   custom elements registered, zero 4xx, screenshot size heuristic (a ~30KB
   screenshot of a game menu = unstyled; ~100KB = styled). To simulate GitHub
   Pages subpath, serve the PARENT dir (`python3 -m http.server` from the dir
   CONTAINING `repo/`), then hit `/repo/` — serving the repo dir itself as
   root silently fakes success.
   - Known env limit: upstreams that reject software GL (`SwiftShader` /
     renderer-string check) can't render their canvas on this GPU-less box.
     Menu + game-logic boot is still fully verifiable; note the limit, don't
     debug it as a bug.
6. **Deploy: GitHub Pages** (user's token already in /data/.git-credentials,
   Bearer form):
   repo via `POST /user/repos` → push → `POST /repos/<o>/<r>/pages` with
   `{"source":{"branch":"main","path":"/"}}` → poll `pages/builds/latest`
   until `built` (~1–2 min). All asset paths must be RELATIVE (`./x`, not
   `/x`) — manifest src, SW cache list, Worker() URL, stylesheet link.
7. **Verify production**: reload in playwright against the live URL; check
   manifest fetch = 200, `navigator.serviceWorker.getRegistration()` truthy
   after one reload (first visit registers, second activates).
   CDN propagation can 404 briefly — re-test before "fixing".

## Pitfalls (all hit for real)
- vite build exit 137 on this box is cgroup memory, not flags. Go esbuild
  immediately; do not iterate heap sizes.
- Unstyled app + duplicated navs + placeholder icons = Tailwind never compiled
  and/or stylesheet not linked. Check both before touching anything else.
- `?worker&inline` under esbuild → runtime "X is not a constructor". Separate
  worker bundle + URL constructor.
- Missing globals (`__ASSET_MANIFEST__`) fail only at game-start time, not
  page load — test the full flow (start a game), not just the menu.
- **Workers reset their own globals at startup AND resolve relative fetches
  against their own script URL** (`/repo/src/worker.js`), not the page —
  `./maps/x` becomes `/repo/src/maps/x` (404). A build-time empty
  `__ASSET_MANIFEST__` define inside the worker also overwrites anything the
  main thread set on globalThis. Full fix that survived production: (a) main
  thread posts `{type:"asset-manifest", manifest}` **synchronously right after
  `new Worker()`** (a ready-handshake can lose the race against the first
  game-start message), with values made absolute via
  `new URL(v, document.baseURI).href`; (b) worker stores it into
  `globalThis.__ASSET_MANIFEST__` and its URL builder prefers absolute
  manifest entries verbatim. Symptom: "Failed to load ./maps/world/manifest.json"
  while curl of the same URL returns 200.
- **Installed-device SW cache poisoning outlives every server-side fix.**
  Cache-first without revalidation caches 404 responses forever, and iOS HTTP-
  caches sw.js itself up to 10 min (GitHub Pages sends max-age=600), so the
  user keeps hitting the old bug after you deploy the fix — localhost tests
  keep passing because they start fresh. Defense in depth that worked:
  (a) version-keyed cache names + skipWaiting()/clients.claim(); (b) network-
  first for JSON manifests, cache-first only for big binaries; (c) app loaders
  fetch with `{cache:"reload"}` plus one plain-fetch retry — defeats any stale
  SW; (d) one-time self-heal: localStorage flag → delete all versioned caches →
  location.reload(). Tell the user: close PWA fully, reopen, let it self-reload.
- **CRITICAL (2026-08-21): loadJsonFromUrl MUST also use cache-bypass.**
  The deployed bundle's `loadJsonFromUrl` method **lacked** the `cache: "reload"`
  patch that `loadBinaryFromUrl` had. If the SW or HTTP cache had a stale 404
  for the manifest, the JSON loader would fail silently (no retry), while the
  binary loader would recover. Manifest fetches are SMALL and CRITICAL — they
  must always use the same cache-bypass + retry pattern as binary loads.
  Patch to apply (search for `async loadJsonFromUrl`):
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
- GitHub Pages subpath breaks every absolute path; make paths relative FIRST,
  then simulate the subpath locally.
- **Carrier/CDN caches can make ALL server-side fixes invisible.** GitHub
  Pages `max-age=600` + Egyptian carrier caches served users a weeks-old
  bundle even from "fresh browsers"; versioned query strings don't help
  because the cached HTML itself is what's stale. Fingerprint which bundle a
  remote user runs from their pasted error (`?v=` + line numbers) before
  debugging. If users still report old-code symptoms after one versioned
  redeploy, migrate to a FRESH PATH (new repo `/app2/`) — an uncached URL is
  the only guaranteed delivery. Worked: frontwar → frontwar2 migration fixed
  instantly what three correct fixes could not.
- **Absolute asset URLs built in JS need the asset manifest, not just relative
  file links.** Engines often have `buildAssetUrl()` returning `/${path}` for
  anything absent from `BOOTSTRAP_CONFIG.assetManifest`. Under a `/repo/`
  subpath those silently 404 → "?" placeholder on every icon, while curl
  checks of files on disk "pass". Populate the manifest with BOTH keys per
  file → `{"img/x.svg": "./img/x.svg", "/img/x.svg": "./img/x.svg"}` for all
  2,600+ shipped files, and regenerate it whenever files are added. Diagnose
  by listing broken `<img>` (`naturalWidth===0`) + 4xx responses in playwright
  against the LIVE URL — disk checks cannot catch this class of bug.
  Regenerator script: `scripts/generate_asset_manifest.py` (writes the
  BOOTSTRAP_CONFIG block into index.html; re-run after adding assets).
- Multiplayer lobby routes (`/lobbies` WS, `/api/*`) need upstream's Node game
  server; static hosting = solo mode only. Say so up front. Cosmetic client
  errors (cosmetics/news/streams/auth fetch failures) are the same class —
  point `jwtAudience` at `"localhost"` so they fail fast instead of DNS-
  hanging on `api.null`.
- Subagents default to writing scratch files in their cwd. On this box that is
  /data (~500MB cap) — one agent filling it kills the gateway AND all sibling
  agents mid-run (happened for real). Always put "write ONLY to /tmp and
  /opt/work — never /data" in every delegate_task context block, and check
  `df -h /data` before dispatching heavy work.

## References
- `references/pwa-build-playbook.md` — full command bank: esbuild client+worker
  invocations, Tailwind v4 CLI, shell template checklist, GitHub API deploy
  sequence, playwright verification snippets, OpenFront→FrontWar worked example,
  worker postMessage handshake + SW cache-poisoning defenses.
- `scripts/generate_asset_manifest.py` — rebuilds BOOTSTRAP_CONFIG.assetManifest
  in index.html (run after adding any assets; see subpath pitfall above).
- `scripts/pwa_smoke_test.js` — production smoke test: broken images, 4xx/5xx,
  undefined custom elements, page errors at mobile or desktop viewport. Run
  against the LIVE URL after every deploy (localhost passes hide this entire
  bug class). Requires playwright; browsers at
  PLAYWRIGHT_BROWSERS_PATH=/opt/work/.pw-browsers.
- Companion skill `pwa-static-hosting` carries the full incident case file
  (`references/frontwar-openfront-case.md`) — live URL, patch points,
  debugging recipes, and honest open-issue status.
