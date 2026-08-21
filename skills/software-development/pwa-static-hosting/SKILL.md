---
name: pwa-static-hosting
description: Use when deploying a web app as a PWA to static hosting.
---

# PWA / Static-App Hosting From a Constrained Box

Class covered: fork/build a client-heavy web app → host it as an installable
PWA on static hosting → verify with headless browsers. Steps marked ✅ were
verified live in production during the FrontWar/OpenFront engagement (case
file: `references/frontwar-openfront-case.md`). That reference has an OPEN
ISSUES section — do not treat its unresolved items as working guidance.

## 1. Build on a ~1GB-RAM box ✅
Rollup/Vite production builds OOM-kill (exit 137) on large TS codebases here —
the cgroup limit (~1GB total) kills them regardless of `NODE_OPTIONS` heap
caps, thread counts, or `--minify false`. Do not retry vite more than once.
**Use esbuild directly** (bundled a 4.8MB client in <1s where rollup never
finished):

```bash
npx esbuild src/client/Main.ts --bundle --outfile=dist/client.js --format=esm \
  --platform=browser --loader:.ts=ts --loader:.tsx=tsx --jsx=automatic \
  --loader:.glsl=text --loader:.vert=text --loader:.frag=text \
  --loader:.css=css --loader:.png=dataurl --loader:.svg=dataurl \
  --loader:.woff2=file --loader:.woff=file --loader:.mp3=file --loader:.json=json \
  --define:process.env.GAME_ENV='"prod"' \
  --define:'import.meta.env.MODE'='"production"' \
  --define:'import.meta.env.PROD'=true --define:'import.meta.env.DEV'=false
```

- Web Workers must be bundled **separately** (IIFE format) — esbuild does not
  implement vite's `?worker&inline`; patch the client's worker-construction
  site to `new Worker("./path")`.
- Tailwind v4 (CSS-first): `npx @tailwindcss/cli -i src/styles.css -o out.css
  --content "src/**/*.{ts,tsx},index.html"`.
- If you hand-build `index.html`, you MUST add `<link rel="stylesheet">`
  yourself — vite normally injects it, and its absence ships a fully unstyled
  app (duplicated navs, placeholder icons).

## 2. Static-shell requirements ✅
Apps bootstrapped by a server template need these replicated as plain globals
in the HTML:
- Every `window.BOOTSTRAP_CONFIG` field the client reads (audit the bundle for
  reads; missing fields surface as bizarre artifacts like requests to
  `api.null`).
- Any build-time `--define` constants expected at runtime
  (`window.__ASSET_MANIFEST__` etc.).

Verify custom elements at **runtime** (`customElements.get(tag)` in a real
browser) — grepping minified bundles for `customElements.define` finds nothing
because tag names are variable references.

## 3. Subpath hosting (GitHub Pages `/repo/`) ✅ — biggest failure class
Root-absolute URLs built inside the app (`/images/x.svg`) 404 under
`https://user.github.io/repo/`. Fixes, in order:
1. Populate the app's asset-manifest hook with an entry for EVERY shipped
   file, value relative (`"./rel/path"`); generate from disk at build time and
   inline into `BOOTSTRAP_CONFIG`.
2. Make all hand-authored HTML/CSS references relative (`./…`), including
   CSS-custom-property background images.

## 4. Web Workers break relative URLs ✅
Workers resolve relative fetches against **their own script URL**
(`/repo/src/worker.js`), not the page — `./maps/x.json` becomes
`/repo/src/maps/x.json` (404). Fix: main thread posts an asset manifest whose
values are made **absolute** (`new URL(v, document.baseURI).href`) to the
worker via postMessage immediately after construction (synchronously — a
ready-handshake can lose the race against the first game-start message), and
the worker's URL builder prefers absolute manifest entries verbatim.

Diagnose main-vs-worker requests with Playwright: `page.on("request")` sees
worker requests too; `r.frame is None` ⇒ worker context.

## 5. Service-worker cache hygiene ✅
- Cache-first SW poisons itself permanently if it ever caches a transient 404.
  Manifest/config JSON must be **network-first**; only big immutable binaries
  (map data, bundles) may be cache-first.
- Version-string every SW release and delete old caches on activate. Bump the
  version whenever shipped behavior changes, or stale devices never heal.
- Precache everything the offline shell needs, including worker scripts and
  sprite/atlas files.
- iOS caches `sw.js` itself (~10 min HTTP cache); installed PWAs keep serving
  a dead SW across reloads. A one-time self-heal flag in localStorage
  (purge caches → reload) recovers devices stuck on a poisoned SW.

## 6. Defeat CDN/carrier stale-JS ✅
GitHub Pages sends `max-age=600`; Egyptian ISPs and mobile carriers cache far
harder. Users on "fresh browsers" still received the previous deploy. Fix,
in escalation order:
1. Content-hash every bundle URL in `index.html` (`client.js?v=<sha8>`,
   `worker.js?v=<md58>`), re-hashing on every change.
2. If users STILL get old code: the cached artifact is the HTML itself, so
   versioned inner URLs never get seen. **Migrate to a fresh path** — new repo
   (`/app2/`) or new domain. Nothing has ever cached an unused URL; this
   instantly fixed what three rounds of server-side fixes could not.
3. Diagnose which bundle a remote user actually runs from their own error
   report: stack-trace line numbers + `?v=` query strings in their pasted
   error are fingerprints — compare against the deployed bundle before
   debugging anything else ("fixed on server" means nothing if the device
   runs week-old code).

## 7. Deploy + verify loop ✅
GitHub Pages via API: create repo → push → `POST /repos/{o}/{r}/pages`
(source main, root) → poll `GET .../pages/builds/latest` until `built` →
verify the **live URL** with Playwright (never trust local-only tests: they
pass while users see stale/broken builds). Verify broken-image count
(`img.complete && naturalWidth===0`), 4xx responses, custom-element
registration, and one full user flow. Reproduce mobile bugs with
`p.devices["iPhone 13"]` emulation — some failures only appear there.

## Conduct rules for this environment (user-mandated)
- **Never write to `/data`** — tiny quota volume; filling it kills the gateway
  and the user's access. Work products go to `/tmp` or `/opt/work`;
  deliverables land in `/data/workspace` only when the user asks for a copy.
- This applies **to subagents**: spell the write-location ban out explicitly
  in every delegation `context`. An unbounded agent defaulting to `./` filled
  the disk mid-run and killed an entire parallel QA fleet.

## Reference
- `references/frontwar-openfront-case.md` — case file: state map, exact patch
  points, debug transcripts, resolution status of each incident (worker
  manifest 404 class: RESOLVED via fresh-path migration; final map render on
  the user's device: still unconfirmed — WebGL layer, not the manifest bug).
