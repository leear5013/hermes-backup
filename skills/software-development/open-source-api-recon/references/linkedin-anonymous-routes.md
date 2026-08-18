# LinkedIn Anonymous Access Routes (tested 2026-08-18, datacenter IP, plain curl)

Context: the web-research skill's blanket claim "LinkedIn blocks ALL anonymous access" is
outdated. These three routes return real data with no login, no cookies, no CAPTCHA —
just a browser User-Agent. Verify them fresh before relying long-term (LinkedIn changes
walls); each probe below is a one-liner.

## 1. Guest jobs search API — the "Jobs tab" without login
```
curl -s -m 35 -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
  "https://www.linkedin.com/jobs-guest/api/seeMoreJobPostings/search?keywords=Data%20Engineer&location=&f_WT=2&start=0" \
  -o /tmp/li.html -w "HTTP %{http_code} size %{size_download}\n"
```
- HTTP 200, ~27KB of HTML job cards. Parse with BeautifulSoup for
  `a.base-card__full-link[href*="/jobs/view/"]` (job URL), `span.sr-only` (title),
  `span.job-search-card__location` (location).
- `f_WT=2` = remote-only filter. `start=N` paginates.
- Also used by the `python-jobspy` library's LinkedIn provider (JobSpy ≥1.1.x):
  `scrape_jobs(site_name=['linkedin'], search_term=..., results_wanted=N, remote=True, country_indeed='egypt')`
  — pass a VALID country string for `country_indeed`; empty string raises ValueError.
- The full search page (`/jobs/search?keywords=...`) is also HTTP 200 (~270KB) but the
  guest API variant above is smaller and easier to parse.

## 2. Company pages — jobs posted as company updates
```
curl -s -m 35 -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
  "https://www.linkedin.com/company/saragossa/" -o /tmp/co.html -w "HTTP %{http_code} size %{size_download}\n"
```
- HTTP 200, ~350KB. The page embeds recent post text as `"text":"..."` JSON blobs and
  `urn:li:activity:<18-digit-id>` IDs (extract with regex).
- This is how you read HR posts that live ONLY on the company feed — recruiters who
  "post the job, not the job posting".
- NOTE: `/company/<name>/posts/` itself 302-redirects to a login wall. The main
  company page is the open one.

## 3. Post permalinks — full body of a specific post
```
curl -sL -m 45 -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
  "https://www.linkedin.com/feed/update/urn:li:activity:<ID>/" -o /tmp/p.html -w "HTTP %{http_code} size %{size_download}\n"
```
- HTTP 200, ~280KB, FULL post text in `<title>` and `og:description` meta tags.
- The short form `linkedin.com/posts/<slug>_<ID>` returns 404 — use the
  `/feed/update/urn:li:activity:<ID>/` form.

## Still blocked anonymously (as of 2026-08-18)
- Personal profiles `/in/<handle>/` → HTTP 999 bot-wall (all UAs incl. Googlebot).
- `/company/<name>/posts/` → 302 → `linkedin.com/uas/login`.
- Voyager API (`/voyager/api/...`) → 403 "CSRF check failed" without a session.
- Community consensus (r/hermesagent, r/webscraping): for logged-in LinkedIn work from
  a VPS, use **camoufox + noVNC** (stealth Firefox, manual one-time login, survives
  CAPTCHAs better than raw Playwright); use a THROWAWAY account for high-volume scraping
  — LinkedIn bans; never your main account. Paid fallbacks: Apify LinkedIn actors,
  Bright Data APIs, ghostgenius-style third-party APIs (~100 free trial credits).

## ToS / ethics note
Public data on pages designed to be public is generally OK to read; bulk scraping,
account-circumvention, and using scraped data to spam/automate applications against
LinkedIn's ToS is where the risk sits. Keep volume low and human review in the loop.
