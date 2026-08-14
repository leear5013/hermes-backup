---
name: anti-detect-browsers
description: "Use when evaluating anti-detect browsers."
---

# Anti-Detect / Stealth Browsers

Evaluating, installing, and testing browsers that spoof fingerprints to bypass bot detection.

## When to Use

- User asks whether a stealth browser (camoufox, patchright, nodriver, etc.) can bypass bot protection, or asks for signup/trial automation on a protected site
- Scraping or automation hitting Cloudflare/Turnstile/DataDome walls
- Installing or testing an anti-detect browser on a headless server

## Core mental model: detection layers

Bot detection = **browser layer** (fingerprint) + **IP layer** (reputation) + behavior + account gates. Fingerprint tools only win the browser layer:

1. **Datacenter IPs get blocked regardless of fingerprint.** Community consensus quote: "Datacenter IPs = instant block." Residential/mobile proxies are usually the actual unlock, not a better browser. Dev.to (arsonxdev): "Anti-detect browsers (Camoufox, not Chromium) are required for Cloudflare Turnstile. Datacenter IPs will block you from even loading some CAPTCHAs (especially Google's)."
2. **Account gates are NOT bypassable by any browser tool:** SMS verification (real number required), payment card entry, and site abuse rules (mass trial signups get flagged/killed even when they succeed).
3. **Gmail/Google is the hardest wall** — phone + CAPTCHA + datacenter-IP block at creation. No legitimate automated path; don't offer one.

## Landscape (2026)

| Tool | Base | Notes |
|---|---|---|
| camoufox | Firefox | #1 OSS anti-detect. C++-level spoofing (WebGL, AudioContext, WebRTC, screen) before JS sees it. Playwright/Juggler protocol. Losing edge vs heavy anti-bot (DataDome/Kasada) because OSS fingerprint code is readable by vendors. |
| patchright | Chromium | Source-level patch of Playwright JS. Weaker vs heavy fingerprinters, easier for Chromium workflows. |
| undetected-chromedriver | Chromium | Old, Selenium-only, shows its age. |
| nodriver | Chromium | Lightweight, no CDP. Most-reported failures lately (r/webscraping thread "nodriver failure patterns"). |
| Commercial (GoLogin, Kameleo, Multilogin, DICloak) | — | Managed fingerprints + integrated proxy tooling, paid. |

## camoufox forks that matter (Web Scraping Club LAB #106, Jun 2026 — actually tested vs DataDome)

- **JWriter20/camoufox** — fixes WebRTC real-IP leak behind HTTP proxy (official build leaks via srflx STUN candidate). Pragmatic pick for proxy setups.
- **LeooNic/camoufox** — content-aware canvas noise defeating the WWW'25 Pixel-Recovery attack. Best code on paper; ships Windows-only Firefox 149 binary that won't launch under Playwright (their issue #1 open).
- **camoufox-reverse (WhiteNightShadow)** — PropertyTracer at SpiderMonkey level showing which DOM properties detectors read. A tracer, not an evader.
- Detail, quotes, config flags: `references/camoufox-2026-fork-testing.md`

## Install on headless Debian server (validated 2026-08)

```bash
mkdir -p /opt/work/<name> && cd /opt/work/<name>     # NEVER /data — 500MB cap
/opt/venv/bin/python -m venv venv && venv/bin/pip install camoufox
XDG_CACHE_HOME=/opt/work/<name>/cache venv/bin/python -m camoufox fetch
#   ^ REQUIRED: camoufox fetch defaults to ~/.cache/camoufox (= /data → hits 500MB cap, "No space left on device")
apt-get install -y libgtk-3-0 libasound2t64 libdbus-glib-1-2 libxt6t64 libx11-xcb1 \
  libxcomposite1 libxdamage1 libxrandr2 libgbm1 libpango-1.0-0 libcairo2 libnss3 \
  libxss1 libxcursor1 libxfixes3 libxinerama1 libxext6 libxi6 libatk-bridge2.0-0 \
  libatk1.0-0 libgdk-pixbuf-2.0-0 libglib2.0-0 libfontconfig1 libfreetype6
```

- Debian 13 renamed many libs with a `t64` suffix — guessing names fails; verify with `apt-cache search <name>` (e.g. `libasound2t64` not `libasound2`, `libdbus-glib-1-2` not `-2t64`, `libxt6t64`).
- Sanity check: `from camoufox.sync_api import Camoufox; with Camoufox(headless=True) as b: p=b.new_page(); p.goto("data:text/html,<h1>x</h1>")` — launches fine headless once GTK libs are in.

## Stealth probe design (what detectors actually read)

- `navigator.webdriver`, UA/platform/vendor, `navigator.languages`
- `hardwareConcurrency`, `deviceMemory`, screen geometry / colorDepth / DPR
- Canvas fingerprint (toDataURL of text+shapes), WebGL renderer via `WEBGL_debug_renderer_info`
- WebRTC ICE candidates (real-IP leak check) — must run on a real https origin, NOT about:blank/data: (content injection is inactive there; LAB #106 hit this false-positive)
- Compare against a vanilla Playwright/Firefox baseline to see the actual delta

## Pitfalls

- `camoufox fetch` writes to `~/.cache/camoufox` — on this box HOME=/data (500MB cap). Always set `XDG_CACHE_HOME`.
- First launch fails `XPCOMGlueLoad ... libmozgtk.so: libgtk-3.so.0: cannot open shared object file` → missing GUI libs, install list above.
- Heavy probe pages (WebRTC/STUN + long timers) hung headless camoufox and killed the Playwright pipe with `write EPIPE` in a restricted container (2026-08-14, unresolved). Keep probes minimal with timeouts; a browser that crashes on one heavy page is NOT proof the tool is broken — retry with a stripped page before concluding anything.
- Don't pipe `curl` output straight into an interpreter (`curl | python`) — the Hermes security scanner flags it; save to file then parse.
- Distinguish wrapper projects from engines: jo-inc/camofox-browser is a Node REST wrapper around Camoufox (element refs, a11y snapshots, cookie import, proxy+geoip), not a new engine — same underlying detection capability.
