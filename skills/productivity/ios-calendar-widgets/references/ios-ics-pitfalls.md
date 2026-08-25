# iOS ICS pitfalls & import recipes (verified 2026-08)

## Failure modes
1. **Safari refuses .ics from catbox.moe** — catbox serves `.ics` as
   `application/octet-stream` (and `HEAD` even reports `content-length: 0`).
   Safari shows "Safari cannot download this file". ALWAYS `curl -sSI` the URL
   first and check `content-type` before sending a download link to the user.
2. **0x0.st uploads disabled** — "uploads disabled because it's been almost
   nothing but AI botnet spam" (permanent state at time of writing). Don't plan
   around it.
3. **tmpfiles.org works** — POST multipart `file=@x.ics` → JSON
   `{"status":"success","data":{"url":"https://tmpfiles.org/<id>/<name>"}}`.
4. **Third-party calendar apps (e.g. "Eva") import the ICS but their events do
   NOT appear in Apple's Calendar widget** — widget reads Apple Calendar only.
   Diagnose by asking: "does Apple's Calendar app show today's event?" before
   walking through widget steps.

## Import recipes (iOS)
- Chat attachment → Save to Files → tap file → **Add All** → pick calendar.
- If Files preview has no Add All (version-dependent): share → Mail to self →
  open in Mail → tap attachment → **Add All**.
- Safari download route (when server MIME is correct e.g. `text/calendar`):
  open URL → Downloads → tap .ics → Add All.
- Zero-download rebuild via Shortcuts (pre-installed):
  1. Text action — paste base64 of the .ics (must be served as text/plain,
     catbox .txt works since it's served as text).
  2. Base64 Encode — tap "Encode" inside → switch to **Decode**.
  3. Set Name — e.g. `duty.ics`.
  4. Save File — default location.
  5. ▶️ run → Files → tap duty.ics → **Add All**.

## Widget placement (iOS 16+)
- Home screen: long-press empty area → **＋** → search Calendar → small
  "Up Next" → Add Widget → Done.
- Lock screen: long-press lock screen → Customize → tap widget row below
  clock → Calendar → Up Next.
- Calendar widget shows today's single all-day event; flips at midnight.
- Photo widgets (heatmap PNG): Widgetsmith Premium Photo-from-album, or
  built-in Photos album widget (rotates). Static — no live refresh without
  Scriptable/Shortcuts automation. The Calendar ICS route is the only
  truly-live zero-install option.
