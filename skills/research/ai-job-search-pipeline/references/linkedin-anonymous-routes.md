# LinkedIn Anonymous Access — Worked Recipe (verified 2026-08-18, datacenter IP)

Three anonymous endpoints work with a desktop Chrome User-Agent + `Accept-Language: en-US,en;q=0.9`.
Personal profiles are the only hard block. All URLs below tested with plain `urllib`/curl.

## 1. Guest jobs search API (the jobs tab)

```
GET https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search
    ?keywords=data+engineer&location=&f_WT=2&f_TPR=r86400&start=0
```
- `f_WT=2` → remote filter. `f_TPR=r86400` → last 24h (r604800 = 7d).
- `start=0` first page; each page ~10 cards.
- Returns HTML with one `<div class="base-search-card ... job-search-card">` per job.

### Parsing (Python regex — do NOT use a JSON parser)
Split cards on `base-search-card--link` — **not** `base-search-card` (the shorter
token appears in `base-search-card__title` etc., fragmenting every card).

Per card:
- title: `<span class="sr-only">\s*\n?\s*(...)</span>` (the visible h3 is empty-ish;
  the sr-only span holds the real title)
- company: regex `hidden-nested-link"[^>]*>\s*([^<]+?)\s*</a>` with `re.S` — the name
  is the anchor's TEXT (`> DLA Piper </a>`), NOT its href (href is a tracker link like
  `https://uk.linkedin.com/company/dla-piper?trk=public_jobs_jserp-result_...`)
- location: `job-search-card__location">([^<]+)<`
- url: `href="(https://www\.linkedin\.com/jobs/view/[^"]*)"` → strip `?position=...`

Known-good sample output: `Data Engineer @ DLA Piper — San Francisco Bay Area`.

## 2. Company page (HR job-posts as company updates)

```
GET https://www.linkedin.com/company/<slug>/     # e.g. /company/confluent/
```
HTTP 200 (~350KB). Extract post IDs: `urn:li:activity:(\d+)` (dedupe, keep order —
first = newest). ~10 IDs per company page. Post bodies live in embedded JSON as
`"text":"..."` blobs (unescape `\n`).

Note: `/company/<slug>/posts/` → 302 to login. Only the base company page is public.

## 3. Post permalink (full post body, no login)

```
GET https://www.linkedin.com/feed/update/urn:li:activity:<ID>/
```
HTTP 200. Full post text in `<meta property="og:description" content="...">`
(html-unescape once). og:title has the author line. This is how you catch
"job posted only as a LinkedIn post" (HR posts): company page → IDs → permalink →
filter text for hiring signals (`hiring|we're looking for|apply|open role|join our team|
vacancy|salary|intern|opportunity`).

Tested: a real HR hiring post ("WE'RE HIRING: TERRITORY OWNER" from Vezeeta/Egypt)
was caught this way.

### Personal-profile post permalinks → LOGIN WALL (HTTP 200 trap)
A company post permalink returns the body anonymously, but a post that lives on an
INDIVIDUAL's profile (`.../posts/<handle>_...` or `/feed/update/urn:li:activity:<ID>/`
for a personal post) does NOT. It returns HTTP 200 with `pageKey: d_registration-cold-join`
and og:title/og:description replaced by "Sign Up | LinkedIn" — the post text is entirely
absent from the HTML. Do NOT trust HTTP 200 alone for personal posts: check for the
wall marker (`pageKey` / `d_registration-cold-join` / a `<title>Sign Up` tag) before parsing.

**Unlock (verified): a valid `li_at` session cookie** sent as `Cookie: li_at=<token>`
removes the wall on ALL post permalinks (returns the full ~1.4MB authed HTML, no
signup marker — the `pageKey: d_registration-cold-join`/`<title>Sign Up` markers are gone).
- Store the cookie at /opt/work/.li_at (chmod 600) — a user-account credential; handle
  with care. It unlocks recruiter personal posts that are otherwise invisible.

**Status of EXTRACTING the post text from the authed page — PARTIALLY UNRESOLVED.**
Do not assume a simple recipe works yet:
- og:description / og:title are BLANK on the authed page (do not rely on meta tags).
- The authed HTML is a JS-shell + embedded Voyager JSON. Simple regex searches for the
  post wording and for `"commentary"`/`attributedTextBody` value blobs did NOT yield the
  post text — the only `commentary`/`attributedTextBody` hits were Voyager *schema type
  definitions* (`com.linkedin.voyager.dash...Component`), not the rendered update. The
  actual post loads via a client-side XHR after render, so it is NOT in the initial HTML.
- Voyager REST API `/voyager/api/feed/updates/urn%3Ali%3Aactivity%3A<id>` → HTTP 403
  CSRF when sent with ONLY `Cookie: li_at=<token>` (no session token). A bare li_at is
  therefore NOT sufficient to talk to Voyager. Obtaining a paired session `JSESSIONID`
  + `csrf-token` (e.g. from a logged-in home-feed fetch) is the plausible next step but
  was NOT validated before this session ended — treat it as a hypothesis, not a recipe.
- Bottom line: the cookie reliably REMOVES the wall; reliably READING the personal-post
  body from it is an open problem. If you need the text and this is still unsolved, fall
  back to a logged-in headless browser (camoufox) driving the real page, or ask the user
  to paste the post content.

## 4. What stays blocked
- `/in/<handle>/` personal profiles → HTTP 999 bot-wall (even Googlebot UA).
- `/company/<slug>/posts/` → 302 auth redirect.
- Google Jobs (`google.com/search?...ibp=htl;jobs`) → 302 `sorry/index` captcha.
- Voyager API (`/voyager/api/...`) → 403 CSRF without real session cookies.

## Workarounds for the blocked parts (from Reddit consensus)
- camoufox + noVNC for a logged-in stealth browser (VPS datacenter IPs still get
  CAPTCHAs; a private/residential IP helps). `/data/camoufox` exists on this box.
- Apify actors (linkedin-jobs-scraper, apimaestro) — some free tiers; apimaestro
  was cited as "currently free" on Reddit for post scraping.
- n8n-job-hacker (github.com/sirlifehacker/n8n-job-hacker) — LinkedIn jobs scrape →
  resume customization → hiring-manager contact finder.
- python-jobspy: `scrape_jobs(site_name=['linkedin'], search_term=..., remote=True,
  country_indeed=<valid country>)` — requires a non-empty country string or ValueError.

## Rate-limit etiquette
~1-2.5s sleeps between requests; a full 30-company × 2-4 posts crawl takes ~4-6 min.
Company page fetches occasionally 429/blank — retry once, then skip.
