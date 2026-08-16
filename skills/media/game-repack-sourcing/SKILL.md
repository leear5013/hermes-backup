---
name: game-repack-sourcing
description: "Safe repacked-game sources: FitGirl/DODI vs scam sites."
version: 1.0.0
---

# Safe Game Repack Sourcing (piracy hygiene)

## When to use
- User asks where to download a game "for free", whether a site (e.g. ankergames) is safe, or which repacker to use (FitGirl vs DODI etc.).

## Trusted tier (community-vetted, r/PiratedGames megathread)
- **FitGirl Repacks** — `fitgirl-repacks.site` (THE only official domain)
- **DODI Repacks** — `dodi-repacks.site` (official; own subreddit r/dodirepack)
- **ElAmigos** — pre-installed / DDL releases
- **SteamRIP** — pre-installed, no-install games
- Master list: r/PiratedGames megathread (`rentry.org/pgames`)

## Hard avoid
- **ankergames** (.net/.me/.my) — confirmed trojan reports (r/CrackSupport), trust score 30–40/100 (PCrisk/ScamAdviser), heavy malvertising
- **Scene-group impersonators** (skidrowreloaded.com, any "CODEX/CPY/SKIDROW" name site) — scene groups have NO public websites
- **IGG Games** — community reports malware uploads since ~2024 ("safe for years ≠ safe now")
- **Any clone of fitgirl-repacks**: .cc, .website, .com, etc.

## Verification workflow (when unsure about a site)
1. `web_search "<site> scam OR legit OR virus"` + check ScamAdviser / PCrisk / malwaretips scan reports.
2. `site:reddit.com` search → fetch threads via Arctic-Shift (see `reddit-content-retrieval` skill) → upvote-weighted consensus on the site.
3. Confirm the official domain (search "<repacker> official site reddit").
4. **Canonical post URL**: fetch the SITE'S OWN search page (`?s=<game>`) and regex the hrefs — never trust search-engine result URLs (tracking params, odd pagination). Example: fetch `https://fitgirl-repacks.site/?s=gta+iv` → regex `href="https://fitgirl-repacks\.site/[^"]+"` → post URL.

## FitGirl page anatomy (what the numbers mean)
- "Original Size" vs "Repack Size": repack is compressed; install decompresses it.
- "Selective Download": optional parts (modpacks, languages) you can skip.
- "Installation takes": CPU-time estimate; progress bar can look frozen — that's normal.
- After-install integrity check = MD5 verification — let it finish.
- `_Wrappers` folder: DXVK/DxWrapper for old games on modern GPUs (stutter fix — the classic GTA IV problem).
- Multi-part DDL: e.g. 28 x ~500MB parts — one corrupt part breaks extraction (torrent avoids this).

## Torrent vs direct download (explain to beginners)
- Direct: many split parts, browser-dependent resume, single-server speed.
- Torrent: one clean folder, auto error-checking, pause/resume, many peers. Recommend **qBittorrent** (qbittorrent.org — free, ad-free).
- At 100% it shows "Seeding" — you may pause; keeping it seeding briefly gives back to the swarm.

## Install steps (non-technical user version)
1. Download torrent → open in qBittorrent → wait to 100%.
2. Open save folder → double-click `setup.exe` → choose a plain path (`C:\Games\...`, NOT Program Files).
3. Wait 15–30 min, let the integrity check run.
4. Launch the game exe; if stutter, drag `_Wrappers/DXVK` contents into the game folder.
5. Windows Defender may quarantine cracked files (false positive) — add an exception or pause real-time protection during install only, re-enable after.

## Owner / site-legitimacy OSINT (when asked "who runs this APK/download site?")
The same risk-verification applies to Arabic modded-APK sites (e.g. mobiltna.com — "موبايلاتنا"). Legit analysis in one pass:

1. **Fetch the site, extract every contact hint**: About (`/about`, "من نحن"), Contact ("اتصل بنا"), Privacy. Strip scripts/styles/WordPress theme boilerplate, then look for `t.me/...`, Facebook, email, and the site's own claim ("© 2026", company-ish name like "موبايلاتنا للتقنية").
2. **RDAP instead of whois** (often uninstalled on servers): `curl -sL https://rdap.org/domain/<domain>` — registrar, creation/expiry dates, status, nameservers. `rdap.verisign.com` redirect is normal for .com.
3. **Read the signals, don't chase the redacted record**: registrar NameCheap/Cloudflare DNS/1–2yr-old .com + a "modded APK" catalog + no Facebook + generic contact = anonymous small operator who hides *by design* (piracy liability). Cloudflare DNS also hides the origin IP — deeper tracing is a dead end without a legal take-down.
4. **Keyword-find the site's real purpose**: a site tied to "مهكر" (modded/patched) APKs is distributing tampered binaries. That's the finding to state — unknown owner + pirated software = malware risk, and reroute demand to official stores or vetted sources (FitGirl/DODI tier above).
5. **The only legal identity route**: DMCA / law-enforcement request to the registrar (NameCheap) — no legitimate way to unmask WHOIS-privacy owners online.

## Pitfalls
- **WHOIS privacy ≠ mystery to "solve"** — it IS the answer (anonymous operator). Don't burn turns on reverse tracing that's a dead end; say so and deliver the risk verdict instead.
- **WordPress/Arabic sites** — contact info hides behind heavy theme boilerplate; strip `<script>/<style>` and the Jannah-theme nav before grepping or you'll match menu items, not the owner.
- **Old domains ≠ trustworthy** — a 2024-registered domain on a content-farm template is a red flag, not a credential.
- Double-check the URL before downloading — clone sites look identical to the real thing.
- No site is 100% guaranteed; official FitGirl/DODI are the community-vetted minimum-risk tier.
- For known-problem games (e.g. GTA IV), older repack versions may support mods better than the newest "definitive" version — read the page's notes before choosing.
