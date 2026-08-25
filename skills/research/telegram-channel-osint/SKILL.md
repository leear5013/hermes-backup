---
name: telegram-channel-osint
description: >-
  Investigate Telegram channel ownership and operators.
version: 1.0.0
author: hermes-curator
license: MIT
metadata:
  hermes:
    tags: [telegram, osint, channels, ownership, footprint]
    related_skills: []
---

# Telegram Channel OSINT (ownership & operator fingerprinting)

For "who runs this Telegram channel / are these two channels the same operator?"
questions — no login, no bot API token required.

## When to Use
- "Who runs this Telegram channel?" / "Are these two channels the same
  operator?" / "Can you dig the admin out of Telegram?"
- Verifying whether a site + Telegram channel belong to one brand
- Comparing operators in a copycat-heavy niche (modded APKs, stores, mirrors)

## Method ladder (cheapest → strongest)
1. **`t.me/s/<handle>` web preview** — public channel messages WITHOUT a client.
   - `curl -A "Mozilla/5.0 ..." "https://t.me/s/<handle>"` → parse
     `class="tgme_widget_message_text..."` divs; `og:title`/`og:description` give
     channel name + pinned info.
   - Channels with **Restrict Saving / private** show only "View in Telegram"
     (0 post divs, no message markers). Recognize this — it means the operator
     hides the web preview; don't loop retrying with different UAs/params.
   - `?before=<large>` and `?embed=1&mode=tme` do NOT bypass the restriction.
2. **tgstat.com/channel/@<handle>** — public stats: subscribers, country, posts,
   sometimes linked channels/ADMIN names. Parse the visible text (JS-only parts
   won't render; treat missing numbers as "no data").
3. **telemetr.io** — analytics mirror; when it redirects to tlmtr.io, the main
   service is down; skip.
4. **Site footprint** — fetch their listed domains, extract:
   - `<title>` / meta description (often brand + niche)
   - Telegram handles (`t\.me|telegram\.me/(\w+)`)
   - Socials: `instagram.com/(\w+)`, `facebook.com/(\w+)`, `x.com/(\w+)`,
     `youtube.com/([\w-]+)` — **same handle across sites/channels = strong link**
   - Emails, cross-linked domains
5. **Shared-template detection** — Arabic modded-APK / storefront niche uses ONE
   copywriting template everywhere (😀 تحديث opener, ✔️ feature checklist,
   ⚙️ إصدار version line, 🔗 تنزيل link, CTA "تفاعلوا مع المنشور وشاركوه").
   Identical style is NOT proof of same operator — it's the genre dialect.
6. **Definitive test** — compare hosted artifacts (APK hashes, file SHA-256) of
   the same app from both sites. Same hash = same uploader. This beats all
   textual analysis.

## Verified behaviors (2026-08)
- `t.me/s/@traidmod` (with @) FAILS; `t.me/s/traidmod` works when public.
- TraidMod's channel hides web preview (only "View in Telegram" + subscriber
  count) → client-side data unreachable; that's a finding in itself.
- `t.me/s/Mobilltna` (public) returns 18 posts — full post text incl. their
  "الموقع الرسمي" (official site) claim in the channel description.
- tgstat.com works over plain curl; telemetr.io temporarily unavailable
  (tlmtr.io redirect).
- catbox.moe .ics uploads fail iOS Safari (see ios-calendar-widgets skill) —
  not relevant here except: don't use catbox for .ics delivery.

## Output discipline
- Distinguish evidence types explicitly: verified scrape vs. user-provided
  screenshot vs. inference. "Same typing style" from a screenshot is weak
  evidence; same APK hash is decisive.
- State what couldn't be checked (e.g. private channel posts) instead of
  filling the gap with guesses.
- Only the user, inside Telegram, can see channel admins — say so plainly and
  offer the artifact-hash test as the external alternative.

## References
- `references/modded-apk-storefootprint.md` — worked example: TraidMod vs
  Mobiltna fingerprint comparison (domains, handles, template, verdict).