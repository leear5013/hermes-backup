# Mobile deployment for the FB watcher (user asked; verified answer)

Scenario: "customer only has a phone — is there no solution?"

## Android → YES, today, zero extra work
**Kiwi Browser** (free on Play Store) is a Chromium fork that loads unpacked
Chrome extensions exactly like desktop Chrome:
1. Download the build zip on the phone, extract it (Files app / ZArchiver)
2. In Kiwi, open `chrome://extensions` → enable **Developer mode** → **Load unpacked**
   → pick the folder
3. Same extension, zero code changes, zero rebuild.

Why this is the product answer: Egypt's smartphone market is ≈85% Android,
so "mobile-only customer" ≈ solved by Kiwi. The customer still uses their own
account/IP/session inside their own browser — the client-side model holds.

## iOS → NO clean client-side path (defer honestly)
- iOS Safari does not support Chrome-style extensions; Apple's extension model
  (Safari Web Extensions) requires an Xcode wrapper + a $99/yr developer account
  — a real build effort for a side product.
- Injecting into the Facebook iOS app is impossible.
- The only real iOS route is a SERVER-side watcher (customer's cookies on our
  infra + residential proxy) — that breaks the zero-liability client-side model
  and adds proxy cost. Position it as a future premium tier with a higher price
  band, not an MVP feature.

## Handoff pattern that works from a phone
GitHub codeload zip URL (`https://github.com/<user>/<repo>/archive/refs/heads/main.zip`)
downloads natively in mobile browsers and unzips on Android — more reliable for
the user than a Telegram MEDIA attachment.
