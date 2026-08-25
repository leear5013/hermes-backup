# Worked example: TraidMod vs Mobiltna (Arabic modded-APK niche, 2026-08)

## Question
Are the providers behind TraidMod (traidmod.org / @traidmod) and Mobiltna
(mobiltna.com / mobilltna.org / @Mobilltna) the same operator?

## Evidence collected
| Signal | TraidMod | Mobiltna |
|---|---|---|
| Domains | traidmod.org, traidmods.com, traidmod.net | mobiltna.com, mobilltna.org, mobillltna.com |
| Telegram | @traidmod (channel: "TraidMod 👑 APK"), site footer @traidmod_org | @Mobilltna ("موبايلاتنا⚡️ تطبيقات وألعاب مهكرة") |
| Instagram | traidmod / traidmod_org | none found |
| Facebook | TraidMods | none found |
| X | traidmod_org | none found |
| Site meta | "متجر ترايد مود لتحميل تطبيقات مهكرة مدفوعة..." | "موقع موبايلاتنا لتحميل تطبيقات مهكرة..." |
| Web preview | hidden (Restrict Saving — "View in Telegram" only) | public, 18 posts visible |
| Post template | 😀 تحديث + app مهكر + ✔️ checklist + ⚙️ إصدار + 🔗 تنزيل + "تفاعلوا مع المنشور وشاركوه" | identical template |

## Interpretation
- **Identical post template is NOT proof of same operator** — it is the genre
  standard across the whole Arabic modded-APK niche.
- **Zero shared handles/domains/socials** → no positive link found externally.
- TraidMod hiding its web preview is a restriction setting, not an ownership
  clue per se.
- Channel admins are only visible inside Telegram (client-side).

## Verdict given to user
"Different operators, same business" — same niche, no shared footprint; but the
definitive test (same APK SHA-256 hosted on both sites) was offered and not yet
run.

## Lessons
- Always offer the artifact-hash comparison as the decisive external test.
- tgstat.com/channel/@<handle> returns a parseable page (subscribers, country)
  over plain curl — worth scraping before concluding "no data".
- Don't burn cycles retrying t.me/s for restricted channels: 0 message markers
  = restricted, permanently (until the operator changes the setting).
