# Camoufox 2026 fork testing — THE LAB #106 detail

Source: https://substack.thewebscraping.club/p/is-camoufox-still-effective-scraping (Web Scraping Club, Pierluigi Vinciguerra, Jun 04 2026). They read the code and ran 4 builds against DataDome (Leboncoin.fr).

## Verdict up top

> "Camoufox does not pass the harder targets the way it used to."
> "When the entire fingerprint-spoofing codebase is public, the anti-bot vendors can read it line by line and build the exact counter-signal."

Not abandoned: dev moved to CloverLabsAI/camoufox (alpha features: per-context fingerprints, hardware spoofing) + VulpineOS/VulpineOS; daijro repo = checkpoint mirror. 750+ forks, most are mirror bots; only 3 touch the anti-detect surface for real.

## The 3 real forks

1. **JWriter20/camoufox** — targeted stealth fixes; headline = closed WebRTC IP leak under a proxy (daijro issue #538), plus real pytest suite (none of the others ship one). THE pragmatic pick.
2. **LeooNic/camoufox** — content-aware canvas noise defeating the WWW'25 Pixel-Recovery attack (Nguyen & Vadrevu), sigma-lognormal humanized mouse engine, RDPBrowser (drives Firefox over Remote Debugging Protocol instead of Juggler). Best code on paper; ships Windows-only Firefox 149 binary that ABORTS at startup under Playwright (`-juggler-pipe` unrecognized). Their issue #1 "fix: port patches and build system to Firefox 149.0" still open. daijro issues #620/#572 cover Juggler init failures. Unusable with the standard stack today.
3. **camoufox-reverse (WhiteNightShadow)** — PropertyTracer at the SpiderMonkey engine layer: records which DOM properties a page reads. An instrument for watching detectors, not a better scraper.

## WebRTC leak mechanics (why JWriter20's fix matters)

- A page opens RTCPeerConnection → STUN server; reads ICE candidates with no permission. `host` candidates carry LAN IP, `srflx` candidates carry REAL WAN IP.
- STUN runs over UDP; an HTTP proxy tunnels only TCP → the STUN request leaves the real interface, the proxy never sees it, and the srflx candidate leaks the real WAN IP even though every HTTP request went through the proxy.
- Official build sets only `media.peerconnection.ice.no_host`. JWriter20 adds: `default_address_only`, `proxy_only_if_behind_proxy`, `proxy_only_if_pbmode`, `obfuscate_host_addresses` → behind a non-UDP proxy, zero candidates gather, nothing to leak.
- Probe result (same Bright Data proxy, geoip=True): official-146 leaked `[srflx] 203.0.113.25` (real WAN), jwriter20-146 leaked nothing.
- **False-positive trap they hit first:** running the RTCPeerConnection probe on `about:blank` showed BOTH builds leaking — because camoufox's content-level injection is not active on about:blank. Must probe on a real https origin.

## Canvas noise: official baseline weakness

- DataDome calls `toDataURL` + `getImageData` (canvas fingerprint). Standard defense = add noise; official camoufox perturbs ~50% of pixels INCLUDING flat fills (9105/18240 interior pixels perturbed) — exactly what a known-pixel check (fill a solid block, read it back, compare) catches.
- WWW'25 "Breaking the Shield" (Hoang Dai Nguyen, Phani Vadrevu): fixed per-session seed+position noise is reversible via Pixel-Recovery. Two fixes defeat it: leave flat regions alone; make perturbation content-dependent (Brave's Farbling approach — the one they couldn't reverse).
- LeooNic implements both; official camoufox canvas noise is OFF by default (`canvas:seed` must be non-zero), and the stock algorithm shows the tell when forced on.
- DataDome read pattern observed via PropertyTracer: ad page = 584 engine-level reads across 35 properties vs 140 across 30 on homepage → heavy protection lives on content pages, not the landing page.

## Where to spend effort

- Fingerprint browser layer ≈ one third of the fight. IP reputation and behavior (human-like mouse/delays) are the others; the article's whole test harness ran proxies + geoip for every build.
- The block-rate test section is paywalled — the fork analysis above is the free portion.
