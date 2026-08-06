# RASD v1 — project reference (built 2026-08)

Location: `/data/workspace/rasd/` (built with the user, Egyptian Arabic product
«رصد RASD» = "watch"). Purpose: watch Facebook groups, detect Arabic service
requests, alert the customer on Telegram with a ready-made reply.

## Business model (user-approved, do not re-litigate)
- NOT a marketplace, NOT a middleman. Customer pays a subscription; the tool
  brings them the leads they want; THEY reply and own the transaction.
- We are software only — no responsibility, no guarantees.
- The customer connects their OWN account + runs the watcher on their OWN
  machine (home IP). Zero account farms, zero proxies, zero liability for us.
- Moat = Arabic dialect understanding (US tools can't match "نقل عفش" /
  "ترحيل" / Egyptian idioms).

## File map
| file | role |
|---|---|
| `arabic_matcher.py` | matching engine: normalize → concepts → buyer/seller → score |
| `telegram_alerts.py` | stdlib-only Telegram sender (urllib) + ready-reply composer |
| `fb_watcher.py` | poller: cookies → mbasic group page → parse posts → match → alert |
| `demo.py` | offline demo of the alert pipeline (no Facebook) |
| `setup_check.py` | validates bot token, auto-saves chat_id from getUpdates |
| `probe_fb.py` | IP-block vs cookie diagnostic (superseded by skill's scripts/fb_probe.py) |
| `run_watcher.bat` | Windows double-click launcher (chcp 65001 for Arabic) |
| `config.local.json` | SECRETS (cookies, token) — gitignored, excluded from zip |
| `config.example.json` | public template |
| `.gitignore` | config.local.json, seen_ids.json, *.log, __pycache__ |

## Config schema (config.local.json)
```json
{
  "cookie_string": "datr=...; sb=...; c_user=...; xs=...; fr=...",
  "groups": ["https://mbasic.facebook.com/groups/<id-or-vanity>/"],
  "business_name": "...", "phone": "...",
  "telegram_bot_token": "...", "telegram_chat_id": "...",
  "poll_min": 25, "poll_max": 55,
  "active_hours": [8, 23],
  "min_score": 70
}
```

## Matcher internals (arabic_matcher.py)
- `normalize()`: NFKC → أإآ→ا → ة→ه → remove diacritics `\u064B-\u0652` and
  tatweel → collapse spaces. Note: normalization maps ة→ه so keyword lists
  should use the normalized forms.
- `CONCEPTS`: dict of niches, each with `label`, `keywords[]`, optional `stem`
  (verb-form fallback, only counted when a buyer signal is present), and
  `seller_terms[]` (concept-specific ad phrases, −25).
- Scoring (from base 60): buyer +20, seller −40, concept seller term −25,
  hot +25, `؟/?` +5, short post (<12 chars) −15. Classify: ≥90 🔥, ≥70 ✅,
  ≥50 ⚠️, <50 ❌ (skip).
- Test suite: 12 SAMPLE_POSTS covering buyer/seller/typo/noise; currently 12/12.
  Two test expectations were corrected during dev: a seller ad (score −5) must
  be ❌, and a price-ask ("كام التكلفة؟") is a 🔥 buyer signal, not plain ✅.

## Verified facts from this build (do not re-test on the VM)
- Telegram Bot API from this environment: works fine.
- Facebook from this VM (cloud/datacenter IP): **impossible** — www gives 400
  even for /login.php with no cookies; mbasic returns tiny `<title>Error</title>`
  pages. Verified cookie sessions also fail. Live FB testing must happen on a
  residential IP (user's home machine), which matches the client-side model.
- r.jina.ai (reader proxy) fetches FB from its own IPs: public groups return
  content, private groups return the login wall → use as a public/private probe.

## Packaging rule
Zip for the user must list files explicitly and exclude config.local.json;
verify with `unzip -l` and grep for the secret filename. The user downloads
the zip and runs `run_watcher.bat` on Windows (stdlib-only Python, no pip).

## Deployment status (as of session end)
- Bot verified: `RasdAgent_bot`, test message delivered to user chat id.
- Cookies received but UNVERIFIABLE from the VM (IP block) — user must run
  setup at home. Target groups are remote-work groups (Data Annotation / Appen)
  → next iteration needs a "remote/data jobs" CONCEPTS pack (ask user what to
  match: job posts, help requests, payout problems).
