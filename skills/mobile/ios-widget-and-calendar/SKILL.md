---
name: ios-widget-and-calendar
description: >-
  Use when user needs iOS widget images or .ics imports.
---

# iOS Widget & Calendar Generation

Server-side generation of iPhone home/lock-screen assets when the user has no
network for app downloads (or wants zero-install solutions). Verified 2026-08:
GitHub-style heatmap widget + 365-day alternating-duty (S/H turns) calendar.

## When to use
- User wants a custom widget image (heatmap, status board, countdown) without installing an app
- User wants a recurring/alternating schedule (S/H turns, chores) visible on the home screen
- Any "make me something that updates daily but I can't download apps" request

## Three artifact types
1. **Widget image PNG** → Widgetsmith Premium Photo widget, or built-in Photos album widget (free). Static — refreshes only when regenerated server-side and re-imported.
2. **Calendar events (.ics)** → THE live offline option. iOS Calendar widget renders today's event automatically, offline, forever. All-day events show on small "Up Next" widget and lock-screen widget.
3. **Live web-widget (local HTTP server)** → tiny Python server rendering today+tomorrow HTML; iPhone Safari opens `http://<host>:<port>` → Share → **Add to Home Screen** → icon opens the live page. Always current, zero re-imports, no Scriptable. Works from any reachable host (LAN PC, Railway with public URL). Script: `scripts/duty_ticker.py` (BaseHTTPRequestHandler, alternating owner from a start date, black/green full-screen HTML). Verified 2026-08: HTTP 200, correct S/H render. Run via terminal background=true (servers never exit); health-check with curl before handing the URL to the user.
   - **When the host has NO public domain** (Railway default: `RAILWAY_URL` empty, only `RAILWAY_PRIVATE_DOMAIN=*.railway.internal` set) → expose the ticker through a **bore.pub public tunnel**: `/tmp/bore local <port> --to bore.pub` prints `remote_port` → URL is `http://bore.pub:<port>`. Full recipe, install steps, and caveats: `references/bore-tunnel-live-widget.md`.
   - **User preference (2026-08, explicit)**: this user asks for "innovate, don't go the same way as last time" on repeat widget requests — propose a genuinely different mechanism (web-widget/tunnel/Reminders) before re-serving the previous .ics trick. The 9999 bar is a new path, not a re-run.

## Generate .ics
- VCALENDAR with one VEVENT per day: `DTSTART;VALUE=DATE`, `DTEND;VALUE=DATE` (next day), `SUMMARY` with owner name, CRLF line endings, fixed DTSTAMP.
- Import: Files app → tap .ics → **Add All to Calendar** (choose a dedicated calendar, e.g. "Turns"). Fallback: Mail attachment → tap → Add All (more reliable on some iOS versions).
- If the user shows a third-party calendar app (e.g. "Eva") displaying the events, the import worked — the system Calendar may still be empty; keep guiding to widget setup.

## Pitfalls (all hit in real use)
- **Catbox/tmpfiles serve .ics as application/octet-stream → Safari "cannot download this file"**, even though the file is valid. First upload can also silently return content-length: 0 — re-upload (as .txt) and curl -I to verify before sending.
- Workaround A (file route): upload base64 text (`.txt`) → Safari opens it → Select All/Copy → Shortcuts: Text → Base64 Encode (tap inside, flip to **Decode**) → Set Name `duty.ics` → Save File → Files → tap → Add All.
- Workaround B (zero files, best): Shortcuts-native loop: **Repeat N** → **Math** `Repeat Index % 2` → **Adjust Date** (Current Date − Repeat Index − 1) → **If** (result = 1) → **Text** "S — Seif's turn" / Otherwise "H — Hesham's turn" → **Add New Event** (All Day ON). Runs entirely on-device, no downloads at all.
- Widget placement: home screen long-press → ➕ → Calendar → small "Up Next"; lock screen: long-press → Customize → widget row. Widget pulls from ALL calendars — warn user; a dedicated calendar keeps it clean.
- Telegram file preview: user must Share → Save to Files before tapping works.

## Two refinements (verified 2026-08-25)

### "Today + tomorrow" single-event pattern
When the user wants the widget to show BOTH today's and tomorrow's duty in
one glance, bake tomorrow into each event SUMMARY instead of a second widget:
`H — Hesham's turn · tomorrow: S — Seif's turn`. One VEVENT per day, SUMMARY
from `owner(today)` + `owner(tomorrow)` — the small "Up Next" Calendar widget
renders both at once, still auto-flips at midnight. Offer this proactively for
alternating schedules; the plain version was the v1, this is the refinement.

### Base64 decode workaround for network-restricted users
When the user's carrier blocks file downloads (0% quota, "Safari cannot download
this file"), the canonical .ics file cannot reach the phone. The reliable path:
1. Upload the .ics as base64-encoded .txt (catbox.moe serves it as text, not
   octet-stream, so Safari opens it).
2. User copies the base64 text from Safari.
3. Shortcuts: **Text** (paste) → **Base64 Encode** (tap inside → switch to
   **Decode**) → **Set Name** `duty.ics` → **Save File**.
4. Files → tap .ics → Add All to Calendar.
Document this alongside the Shortcuts-native loop (Repeat N → Math → Add New
Event) as the two zero-download paths.

## Image sizing (PIL heatmap-style widgets)
- Design on a small grid (cell 9px, gap 2px, pad 8), then upscale NEAREST ×2–3 → crisp GitHub-style look. Produced: small 912×136, medium 1216×182, large 1824×273 (all fine for Widgetsmith photo widgets).
- Dark bg `#000000` + GitHub green ramp (#0e4429 → #39d353) reads well on OLED lock screens.
- Per-cell letters: DejaVuSans-Bold, `anchor="mm"`, white; outline today's cell `#f0f6fc` width 2.

## Scripts
- `scripts/turn_calendar.py` — parameterized alternating-duty .ics + letter heatmap PNG generator.

## Honesty rule
Custom image widgets CANNOT auto-refresh without Scriptable/network — say so up front. The calendar import is the only true offline live option; the HTTP web-widget is the live option when the phone can reach a host.