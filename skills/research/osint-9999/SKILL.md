---
name: osint-9999
description: Run OSINT investigations on people, usernames, or companies.
---

# OSINT 9999 — Master Intelligence Playbook

Operator-grade open-source intelligence with a 9999-experience posture:
systematic, verified, documented, ethical. Grounded in the 2026 OSINT-BIBLE
(450+ tools, 47 sections) + community methodology (r/OSINT, r/cybersecurity,
Trace Labs CTFs).

## Trigger
Any investigation: "find info about <person/company/username/email/phone>",
"who runs X", "is this real", brand/domain recon, breach checks, attribution.
Also use for legit contact routes (never bare refusals).

## The Intelligence Cycle (always, in order)
1. **Direction** — what exactly must be answered? Write 1-3 questions. Stop scope-creep.
2. **Collection** — gather from primary sources first (official pages, original posts, registry data).
3. **Processing** — clean, dedupe, timestamp everything.
4. **Analysis** — cross-check ≥2 independent sources before concluding. Contradictions = flag, don't smooth.
5. **Dissemination** — concise evidence-backed answer with source URLs; separate FACT / INFERENCE / GAP.

## Source Pyramid (trust by layer)
- **Tier 1 (primary)**: official registries (WHOIS, DNS, registry records), official documents, the target's own posts/accounts, court/patent filings.
- **Tier 2**: reputable aggregators (HaveIBeenPwned, crt.sh, archive.org, VirusTotal), news.
- **Tier 3 (never trust alone)**: forums, rumors, AI summaries, reblogs. Validate against Tier 1/2.

## Core toolkit (free, no-login-first)
| Need | Tools |
|---|---|
| Username across networks | Maigret, Sherlock, WhatsMyName, Fingerprint.to (700+ platforms) |
| Email/phone breach | HaveIBeenPwned, DeHashed (careful), LeakCheck |
| Domain/IP/DNS | whois, crt.sh (cert transparency), SecurityTrails, viewdns.info, DNSdumpster, Shodan (free tier) |
| People | LinkedIn (guest API OK), Facebook public, Google/Bing dorks |
| GEOINT/images | Google Lens, Yandex, EXIF (exiftool), SunCalc, GeoSpy |
| Wayback | archive.org (web.archive.org) — ALWAYS snapshot evidence before it disappears |
| Socials | reddit (RSS-first via reddit skill), Telegram (t.me/s preview), X (xurl if authed) |
| Metadata | exiftool, FOCA |
| Crypto | Blockchain.com explorer, Etherscan |
| Frameworks | SpiderFoot, Maltego CE (auto-graph 200+ modules), OSINT Framework (osintframework.com) |

## Investigation recipes
### Person by name
1. Google dork: `"full name" -site:linkedin.com` + variations (Arabic transliterations too)
2. LinkedIn guest profile (company, title, tenure)
3. GitHub: username search, email in commits (`git log` / API commits)
4. WHOIS on personal domains; crt.sh subdomains
5. Facebook public posts/photos (no login)
6. Cross-check: same handle/email across 3+ networks → confident match
7. Archive every finding page (archive.org)

### Company / who-runs-X (like TraidMod case)
1. Website footer → telegram/instagram/facebook/x handles; "official site" claims
2. WHOIS: registrar, creation date, name servers (compare across domains)
3. Telegram: t.me/s/<handle> preview posts; TGStat/Telemetr for geo/sub counts
4. Cross-site socials: same handle on ig/x = same operator
5. Compare artifacts: identical file hashes (APK/PDF), same template text
6. Geo flags: TGStat channel geo (Iraq/Egypt/World) — divergent = different operators
7. **Conclude with confidence levels**: MATCH (hash/account equality), LIKELY (≥2 independent signals), UNKNOWN.

### Email / username
- HIBP breach check → newsletter footprints (leaked via Mailchimp etc.)
- Maigret/Sherlock username enumeration → list profiles
- Google: `"email" "@domain"`, GitHub code search (`user:email` in commits)
- If a service leaks "account exists" (password reset flows) — note existence only, never enumerate further.

## Verification loops (the 9999 differentiator)
- **Never trust one source.** Every key claim needs 2 independent confirmations.
- Timestamp + URL + screenshot/archive for every critical finding.
- Distinguish: what I SAW (primary), what someone SAID (secondary), what I INFER (analysis).
- If a check fails (403, block, 404) — report it, pivot, never fabricate.

## OPSEC (investigator, not target)
- Use a VPN or residential IP for mass lookups (rate limits, blocks).
- No login to target platforms unless authorized; guest views first.
- Never save raw connection strings/tokens; redact ([REDACTED]).
- Batch lookups spaced out; respect rate limits (429 → back off linearly).

## Ethics / legal line (HARD)
- Public information only — no breaking into accounts, no phishing, no credential use.
- No doxxing, harassment, stalking. Trace Labs-style CTF scope only.
- PII handling: minimize, don't publish; use findings for the user's legitimate need.
- Data-breach data: note existence (HIBP-style), never dump/purchase full breach DBs.
- If the request is harassment/stalking → refuse, offer legit contact route alternative.
- In Egypt: respect law; OSINT on public sources for business/security needs is standard work.

## Skill integration (agent mastery)
- Memory separation: findings → vault `memory/` or case file; procedures → this skill.
- Corrections = spec debt: patch this skill when a technique fails or user corrects.
- Always verify with real tool output; never present plausible-but-unrun results.

## References
- OSINT-BIBLE 2026: github.com/frangelbarrera/OSINT-BIBLE (450+ tools, 47 sections)
- awesome-osint: github.com/jivoi/awesome-osint
- osintframework.com (free tools map)
- gralhix.com/list-of-osint-exercises/ (practice CTFs)
- spiderfoot.net (automated entity graph)
- maestro: github.com/soxoj/maigret
