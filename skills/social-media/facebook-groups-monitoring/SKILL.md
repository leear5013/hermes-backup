---
name: facebook-groups-monitoring
description: Use when monitoring Facebook groups for leads.
---

# Facebook Groups Monitoring (client-side model)

## When to use
- Building or iterating a Facebook group watcher (lead alerts, keyword monitoring) — the RASD project lives in `/data/workspace/rasd/`
- Any task that must READ Facebook group posts with a logged-in session
- Diagnosing "why can't I fetch Facebook" from a server/VM

## Core architecture (the model that works)
- **Client-side deployment**: the watcher runs on the ACCOUNT OWNER's machine (their home/residential IP + their cookies). We ship software + setup + keyword packs. No VPS, no proxy farms, no account farms.
- Read-only access only: never post, like, or message from code.
- Human-like timing: random polling intervals (e.g. 25–55s), active-hours window (e.g. 8:00–23:00), occasional long pauses (15% chance of a 60–240s break).
- Alerts go to Telegram (BotFather token + chat_id), one message per match, with a copy-paste-ready reply embedded.

## Critical pitfall: Facebook blocks datacenter IPs
Symptom signature (verify with `scripts/fb_probe.py` BEFORE touching cookies):
- `www.facebook.com/...` → **HTTP 400** for EVERYTHING, even public `/login.php`, with or without cookies
- `mbasic.facebook.com/...` → HTTP 200 but a tiny page whose `<title>` is `Error` (or `خطأ`), no content
- Logged-out requests also 400/Error → the problem is the IP, NOT the cookies
- Do NOT burn time re-copying cookies until the IP block is ruled out.
- Workaround: run on a residential IP (the customer's home machine). This is the architectural reason the product must be client-side.

## mbasic quirks
- `mbasic.facebook.com` is the lightest HTML surface (fewest bot checks) — prefer it over www.
- **Login-wall detection trap**: mbasic does NOT render "Log into Facebook" — it shows a generic Error page. Detect via `<title>Error</title>` OR the literal string "Log into Facebook" in the body, or `login` in the first ~5KB.
- Posts parse via regex: `<a href="/groups/.../(posts|permalink)/<numeric-id>/">...</a>` → strip tags, collapse whitespace, require len ≥ 10 chars.
- Vanity group URLs can return Error on mbasic; resolve the numeric group ID via redirect from www (only works from a residential IP).
- Private groups: content sits behind a login wall even through reader proxies (r.jina.ai returns the login page → group is private; public groups come through). Use r.jina.ai as a quick public/private probe from any IP.

## Cookie extraction (instructions to give the user)
1. Chrome → log in to facebook.com as the account owner (customer account for production, never your own).
2. F12 → Network tab → reload page → click the first request.
3. Request Headers → copy the ENTIRE `Cookie:` value (starts `datr=...; sb=...; c_user=...`).
4. Cookies expire roughly monthly → on "Session expired" logs, redo this step.

## Telegram alert pattern
- Create bot via @BotFather → token like `123456:AA...`
- `getMe` validates the token; `getUpdates` finds the chat_id (empty until the user opens the bot — fall back to the known user chat id).
- `sendMessage` with `parse_mode=HTML`; every alert should embed a ready-made reply line the customer can copy-paste.
- Never print the token in terminal output — read it from the config file.

## Secrets hygiene
- `config.local.json` (cookies + token) must be in `.gitignore`; never pushed, never zipped.
- When packaging a zip: list files EXPLICITLY, then verify nothing leaked: `unzip -l pkg.zip | grep -c config.local` must be 0.
- Redact secrets pasted into chat before any push to GitHub (secret scanning blocks otherwise).

## Arabic dialect matching (RASD technique)
- Normalize before matching: أإآ→ا, ة→ه, remove diacritics and tatweel, collapse whitespace; then substring-match keywords.
- Buyer signals (`عايز/عاوز`, `محتاج`, `في حد يرشح`, `بدور`, `مين يعرف`) vs seller signals (`شركتنا`, `احنا`, `على الخاص`, `كلمونا`, `عروضنا`) — seller posts must be SKIPPED (heavy score penalty), not merely deprioritized.
- Hotness boosters: `ضروري`, `بكرة`, `النهارده`, `كام التكلفة`, `مستعجل` → hot flag.
- Scoring: base 60 on concept match; +20 buyer; −40 seller; −25 concept-specific seller term; +25 hot; question mark +5. Classify: ≥90 🔥, ≥70 ✅, ≥50 ⚠️, <50 ❌ (skip).
- Add per-niche concept blocks in the `CONCEPTS` dict; a `stem` field gives verb-form fallback (`ينضف`→`نظف`).
- Full matcher design, test suite, and config schema: `references/rasd-project.md`.

## Files
- `scripts/fb_probe.py` — run FIRST to distinguish IP-block vs cookie problem.
- `references/rasd-project.md` — RASD v1 file map, config schema, matcher details, packaging/deployment notes.
- `references/mobile-deployment.md` — Kiwi Browser (Android) and iOS limitations.
- `references/github-publish-safely.md` — secret scanning, zip verification, PAT extraction.

## Overlap note
This skill (`facebook-groups-monitoring`, plural) overlaps significantly with `facebook-group-monitoring` (singular). The singular version has richer references/ and scripts/. Consider consolidating into one skill — the singular version is more complete.
