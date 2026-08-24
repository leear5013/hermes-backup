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

## Two artifact types
1. **Widget image PNG** → Widgetsmith Premium Photo widget, or built-in Photos album widget (free). Static — refreshes only when regenerated server-side and re-imported.
2. **Calendar events (.ics)** → THE live option. iOS Calendar widget renders today's event automatically, offline, forever. All-day events show on small "Up Next" widget and lock-screen widget.

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

## Image sizing (PIL heatmap-style widgets)
- Design on a small grid (cell 9px, gap 2px, pad 8), then upscale NEAREST ×2–3 → crisp GitHub-style look. Produced: small 912×136, medium 1216×182, large 1824×273 (all fine for Widgetsmith photo widgets).
- Dark bg `#000000` + GitHub green ramp (#0e4429 → #39d353) reads well on OLED lock screens.
- Per-cell letters: DejaVuSans-Bold, `anchor="mm"`, white; outline today's cell `#f0f6fc` width 2.

## Scripts
- `scripts/turn_calendar.py` — parameterized alternating-duty .ics + letter heatmap PNG generator.

## Honesty rule
Custom image widgets CANNOT auto-refresh without Scriptable/network — say so up front; the calendar import is the only true "live" zero-install solution.