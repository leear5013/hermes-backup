# LinkedIn personal-profile posts — the Voyager wall (verified 2026-08)

Goal: read HR job-posts that only appear on an individual recruiter's **personal**
LinkedIn profile (URLs like `/posts/<handle>_<slug>-<activityID>-<hash>/`), not the
Jobs tab and not the company page. Use case: Hesham wants to catch intern job-posts
shared only as profile updates.

## What works anonymously (no login) — proven
- Guest Jobs API: `https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search`
- Company page: `https://www.linkedin.com/company/<slug>/` → extract `urn:li:activity:<id>`
- Post permalink (company-sourced IDs): `https://www.linkedin.com/feed/update/urn:li:activity:<id>/`
  → full body in `og:description`, no login.
These are covered in the umbrella SKILL.md + `references/linkedin-anonymous-routes.md`.

## The wall (personal-profile posts) — definitive result, NOT a dead end to re-explore
1. **Anonymous** fetch of a personal-post permalink → HTTP 200 but body is the
   **registration wall**: `pageKey: d_registration-cold-join`, title "Sign Up |
   LinkedIn", zero post content in HTML. `robots: noindex` meta present.
2. **With a valid `li_at` cookie** (pasted by user) → login wall gone, HTTP 200, ~1.4MB
   real logged-in page. **But:** og:description/og:title meta tags are BLANK, and the post
   text is NOT in the initial HTML at all (it's delivered by client-side XHR).
3. Regex over `"commentary"` in that HTML finds only **schema/type definitions**, never the
   post body (`"attributedTextBody"` count == 0). Don't fall for it.
4. `/voyager/api/feed/updates/urn%3Ali%3Aactivity%3A<id>`:
   - bare `li_at` (no session pairing) → **HTTP 403 Forbidden**.
   - `li_at` + fresh `JSESSIONID` (from a cookie-jar GET of `https://www.linkedin.com/feed/`)
     sent as BOTH the `JSESSIONID` cookie AND the `Csrf-Token` header, plus
     `x-restli-protocol-version: 2.0.0` → **HTTP 200 OK** … but payload =
     `{"update": {...}, "text": ... "This post cannot be displayed" ...}`, and no author.
   The post content is gated behind **browser-context verification** (fingerprint + JS);
   an authenticated API client from a datacenter IP still can't read it.

## Working alternatives (pick one)
- **camoufox (real stealth browser)** — content will render + be readable because it is a
  real browser context. Setup below. Login once via the live browser (2FA), persist the
  user_data_dir, then automate reading personal posts.
- **User copy-paste**: user opens the post in their browser and pastes text / a screenshot.
  Fastest and zero-risk; fine for a small number of tracked recruiters.

## camoufox setup (all under /opt — never /data)
```
# /opt/work/.home holds all caches (1.3GB browser) — keep it there.
/opt/venv/bin/pip install --no-cache-dir camoufox playwright
# fetch AND every launch MUST share the same HOME, or the launch says
# "CamoufoxNotInstalled: official/stable is not installed" though fetch succeeded.
HOME=/opt/work/.home /opt/venv/bin/camoufox fetch
```
Correct launch API (wrong arg names raise TypeError):
```python
from camoufox.sync_api import Camoufox
fox = Camoufox(headless=True)          # NOT user_data_dir here
browser = fox.start()
ctx = browser.launch_persistent_context(user_data_dir="/opt/work/.camoufox-profile")
page = ctx.new_page(); page.goto("https://www.linkedin.com/", wait_until="domcontentloaded")
```
Notes: `browser.launch_persistent_context` exists on the Playwright object returned by
`fox.start()` (a plain browser `.launch()` has no such method). First launch downloads
and extracts the uBO addon (~progress output) then prints the Firefox version line.
Camoufox v152.0.x-beta installed as of 2026-08.

## Intern / graduate coverage tips for this user
- LinkedIn guest API **ignores the `intern` keyword** (loose matching). Search broad terms
  (`data engineer`, `devops`) with `f_TPR=r604800`/`r2592000` and filter titles for
  `intern|trainee|new grad|skillbridge|graduate` CLIENT-SIDE.
- Big-tech graduate/intern postings cluster in waves (TikTok / ByteDance "2027 Start"
  roles appear ~Aug). Scan back 30 days to catch the wave.