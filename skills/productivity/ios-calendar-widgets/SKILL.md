---
name: ios-calendar-widgets
description: >-
  Build iOS calendar feeds and widgets with zero installs.
version: 1.0.0
author: hermes-curator
license: MIT
metadata:
  hermes:
    tags: [ios, ics, calendar, widget, heatmap, shortcuts]
    related_skills: []
---

# iOS Calendar Feeds & Widgets (ICS + heatmap PNGs)

For "make my iPhone show X without installing an app" tasks: schedule widgets via
the built-in Calendar app (all-day ICS events flip at midnight automatically,
fully offline) and photo widgets via PIL-generated PNGs (Widgetsmith Premium /
Photos widget).

## When to use
- "Whose turn" / alternating-duty schedules on the home/lock screen
- GitHub-style contribution heatmaps as widgets
- Any "generate a calendar feed / widget image" ask with a zero-install constraint
- Importing .ics into iOS from Telegram/Files/Mail/Shortcuts

## ICS generation (the zero-install live solution)
Minimal RFC 5545 calendar, all-day events:
- `BEGIN:VCALENDAR` / `VERSION:2.0` / `PRODID:-//<id>//EN` / `CALSCALE:GREGORIAN`, then one `BEGIN:VEVENT` per day, `END:VCALENDAR`.
- VEVENT fields: `UID:turn-<iso-date>@<id>`, `DTSTAMP:<YYYYMMDD>T000000Z`, `DTSTART;VALUE=DATE:<YYYYMMDD>`, `DTEND;VALUE=DATE:<next-day YYYYMMDD>`, `SUMMARY:...`.
- **All-day DTEND is the NEXT day** (exclusive end per RFC 5545) — classic off-by-one bug.
- **CRLF line endings** (`open(path, "w", newline="")` + `\r\n` joins). LF-only can break strict parsers.
- 365 events ≈ 74KB — fine to send as a file in chat.
- Verify before delivering: read back the first VEVENT, count events, check DTEND.

## Heatmap widget generation (PIL)
- GitHub-style: 5-level palette on black, cell sizes → output ~912×136 / 1216×182 / 1824×273 for small/medium/large.
- Lettered variant: draw S/H initial inside each cell, today's cell outlined white (`draw.rectangle(outline=..., width=2)`), month labels from `calendar.month_abbr`.
- Deterministic fake data (`random.Random(seed)`) until real data source exists.
- Fonts: DejaVu at `/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf` (guard with try/OSError).

## iOS setup paths (user-facing)
- **Calendar widget**: long-press home screen → ➕ → Calendar → small "Up Next" → shows today's single all-day event, flips at midnight. Lock screen: long-press → Customize → widget row → Calendar.
- **Import .ics**: send file via chat → save to Files → tap → **Add All** → pick calendar. If Files preview lacks Add All: Mail attachment fallback.
- **Photo widget**: Widgetsmith Premium (Photo from album) or built-in Photos widget rotating an album. Static image — no live refresh without Scriptable/shortcuts automation; the Calendar route is the truly-live one.
- **Third-party calendar apps caveat**: an app like "Eva" may import the ICS but its events DON'T show in Apple's Calendar widget — the widget only reads Apple Calendar. Always ask "does Apple's Calendar app show today's event?" before walking through widget steps.

## Delivery pitfalls (learned the hard way)
- **catbox.moe serves .ics as `application/octet-stream`** (HEAD returns content-length 0 too) — Safari refuses it: "Safari cannot download this file". Never hand a catbox .ics link as the only path; HEAD the URL first and check content-type.
- **0x0.st uploads disabled** (AI-bot spam) — don't rely on it.
- **tmpfiles.org works**, returns JSON `{"data":{"url":...}}`.
- **Shortcuts rebuild** (when downloads fail entirely): Text(paste base64) → Base64 Encode (switch to Decode) → Set Name(duty.ics) → Save File. Requires the content as text — host the base64 as a .txt that serves `text/plain`.

## Scripts
- `scripts/turn_schedule.py` — one command: alternating-duty `.ics` (N days) + lettered heatmap PNG with today outlined. Args: start date, days, --letters, --names, --out.

## References
- `references/ios-ics-pitfalls.md` — full failure modes + import recipes with exact taps.
