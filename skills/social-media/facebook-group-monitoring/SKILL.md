---
name: facebook-group-monitoring
description: Monitor Facebook groups for leads or keyword alerts.
---

# Facebook Group Monitoring (lead alerts)

## When to use
- Building a "Groups Watcher"-style product: monitor FB groups → alert on matching posts (Arab-market lead-gen is this user's recurring use case)
- Any attempt to fetch Facebook content from a server/VPS
- Keyword/dialect lead detection for Arabic-speaking markets

## Architecture: client-side ONLY (verified this session)
Facebook refuses datacenter/cloud IPs. Evidence from VPS testing:
- `www.facebook.com` → HTTP 400 even for the PUBLIC login page (no cookies involved)
- `mbasic.facebook.com` → HTTP 200 but generic title "Error"/"خطأ" — no content, no login wall
- `r.jina.ai` reader proxy → login wall for private groups (content is behind auth anyway)

**Conclusion:** cookie-based fetching only works from a residential IP with a real browser session → the watcher MUST run inside the customer's own browser (their account, IP, session). This is simultaneously the product win: zero ban risk for us, zero proxy/infra cost, customer is responsible for their own actions.

## Product rule (user-mandated): ZERO customer friction
The customer's total effort must be: **install once + open the group page**. NO Python, NO cookie copying, NO config files, NO .bat scripts, NO command line. Anything more was explicitly rejected by the user as "تقريف" (burden) — "بتعمل سيستم لراجل علشان تريحه ولا علشان تقرفه". One-time bot-token paste in a popup is the maximum acceptable setup.

## Diagnose before touching cookies
Run `scripts/fb_probe.py` FIRST whenever Facebook fetching fails — it distinguishes a datacenter-IP block from bad cookies in ~10 seconds. Signature of an IP block (all verified from a VPS):
- `www.facebook.com/login.php` — public endpoint, NO cookies — still HTTP 400
- `mbasic.facebook.com` — HTTP 200 but tiny (~7KB) page with `<title>Error</title>` / `خطأ`, no content
- Logged-out and logged-in requests fail identically → the IP is the problem; re-copying cookies is wasted time.

Private-group probe from any IP: `https://r.jina.ai/<group-url>` returns the FB login page for private groups (content is behind auth), actual posts for public ones. Use it to check group visibility without a session.

Cookie extraction (only meaningful from a residential IP): Chrome logged in as account owner → F12 → Network → reload → click first request → Request Headers → copy the entire `Cookie:` value (starts `datr=...; sb=...; c_user=...`). Cookies expire roughly monthly — support docs must include the refresh step.

## Chrome Extension (MV3) pattern — the working recipe
Files (see templates/manifest.json):
- `manifest.json` — permissions: `storage`, `alarms`; host_permissions: `https://*.facebook.com/*`, `https://api.telegram.org/*`; content_scripts matches: `https://*.facebook.com/groups/*`
- `matcher.js` — PURE logic, no chrome APIs → unit-testable in node
- `content.js` — injected in group pages: debounced `MutationObserver` on `document.body` + initial scan of `[role="article"], article, [data-pagelet*="Feed"]`; dedupe by text-hash; `chrome.runtime.sendMessage({type:"posts", posts})`
- `background.js` — service worker; `importScripts("matcher.js")`; onMessage → `matchPost` → `fetch` Telegram API (JSON body, parse_mode HTML)
- `popup.html/js` — settings (tg_token, tg_chat, business, phone, min_score) into `chrome.storage.local`; Arabic RTL UI

Load unpacked: `chrome://extensions` → Developer mode → Load unpacked. Publish: Chrome Web Store ($5 one-time dev fee) → customer clicks "Add to Chrome".

## Telegram alert integration
- Bot: @BotFather `/newbot` → token
- chat_id discovery: call `getUpdates`, read `result[].message.chat.id` (or reuse the user's known Hermes chat id — it works if the user has messaged the bot)
- Send: `https://api.telegram.org/bot<TOKEN>/sendMessage` with `parse_mode=HTML`, `disable_web_page_preview=true`
- Alert format that sells: severity emoji + concept label + post text + group + link + **ready-made copy-paste reply** (business name + phone). The ready reply is the differentiator.

## Arabic dialect matcher (reusable technique)
Full concept dictionary + signals in `references/arabic-matcher.md`. Essentials:
- `normalize()`: أ/إ/آ→ا, ة→ه, ؤ→و, ئ→ي, strip tatweel + diacritics, fix common typos ("عفس"→"عفش")
- Concepts: `{label, keywords[], stem, seller_terms[]}` — stem fallback counts ONLY when a buyer signal present
- Scoring: 60 base; +20 buyer; −40 seller; −25 concept seller_terms; +25 hot; +5 question mark; −15 very short
- Classify: ≥90 🔥 hot / ≥70 ✅ clear / ≥50 ⚠️ maybe / else ❌ skip (seller ads score −5..20 → skipped)
- Keep Python and JS ports in sync; run the SAME fixtures through both

## Testing before delivery
- Unit-test the pure matcher in node FIRST: `node scripts/test_arabic_matcher.js <path/to/matcher.js>` (fixtures: 16/16)
- Bot check: getMe → getUpdates → sendMessage test before wiring anything
- Zip packaging: verify secrets excluded — `unzip -l` and confirm `config.local.json`/`seen_ids.json` absent

## Pitfalls (learned the hard way)
- **mbasic "Error" title ≠ login wall**: a refused/blocked session returns 200 with title "Error"/"خطأ". Checking for "Log into Facebook" is NOT enough — always check the `<title>`.
- Cookies expire (~1 month) — support docs must include the refresh step.
- Never debug cookie validity from a VPS — it fails for IP reasons unrelated to the cookies; you can't distinguish "bad cookies" from "blocked IP" there.
- Secrets (cookies, tokens) never in git or zip; `.gitignore` must list `config.local.json`, `seen_ids.json`.
- Content-script dedupe by text-hash, not post IDs — FB post IDs are unstable across renders.
- `zip` may not exist on the box; use Python's `zipfile` module instead.
