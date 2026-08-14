---
name: egypt-business-research
description: "Use when researching companies in Egyptian cities."
version: 1.0.0
author: Hermes
license: MIT
metadata:
  hermes:
    tags: [egypt, companies, business-directory, yellowpages, 140online, research, jobs, overpass, osm]
    category: research
    requires_toolsets: [terminal, web]
---

# Egyptian Business & Employer Research

Discover, verify, and map companies (or employers) in Egyptian cities — especially
provincial governorate capitals where web coverage is thin and directories are the
only reliable ground truth.

## When to Use

- "What companies do X in <Egyptian city>?" (data analysis, software, marketing, ...)
- Verifying a local Egyptian business (address/phone/activity cross-check)
- Mapping employers in a governorate for job hunting
- Any company/market research confined to Egypt

## Core insight: category reality-check

In provincial cities, narrow categories often DON'T exist as such ("data analysis
company" in Shebin El Kom = none — verified). Never answer "none found" and stop.
Map the **adjacent categories** that actually do the work: software/IT houses, ERP &
accounting-software vendors, digital-marketing agencies, government MCIT "Creativa"
innovation hubs, and university AI/ML communities (e.g., PIE & AI / DeepLearning.AI
chapters). Report the gap honestly, then deliver the adjacent opportunities.

## Workflow

1. **Search Arabic AND English.** DDG indexes Arabic poorly; Arabic queries surface
   yellowpages/local listings that English queries never see. Run both:
   - `<topic> <city>` / `<topic> <city> شركة OR شركات` / `شركات <topic> <city>`
   - Job-market angle: `wuzzuf` / `tanqeeb` / `LinkedIn jobs` + city name (+ Arabic).

2. **Business directories — the gold sources** (in order):
   - **Yellow Pages Egypt category pages**: URL shape
     `yellowpages.com.eg/ar/category/<city-slug>-<category-slug>/<id>` — e.g. programming
     in Shebin El Kom = `شبين-الكوم-برمجة/3294`. The category page lists every company
     with street address; trafilatura extracts it without JS.
   - **140online.com** (`/company.aspx?CompanyId=X`) — phones + full addresses.
   - Cross-check with: `eg.kompass.com`, `dalil140.com`, `existedin.com`, official site.

3. **Verify each candidate on 2+ sources** (LinkedIn company page + official website +
   directory phone). Small houses often live on Facebook only. Distinguish HQ-in-city
   vs branch/job-post-only: a Cairo company posting a "Shebin El Kom" job ≠ an office there.

4. **OSM/Overpass ground truth** (optional — see pitfalls: coverage is sparse in Egypt).

5. **Deliver**: numbered verified list — name (Arabic + transliteration), street address,
   phone, one-line "what they actually do" — then the honest gap statement + the
   adjacent-opportunity translation, with source links.

## Pitfalls

- **Overpass main instance** (`overpass-api.de`) times out at peak ("The server is
  probably too busy") → retry the same query on **`overpass.kumi.systems`** (verified
  2026-08). Post body via `--data-urlencode "data@file.ql"` to avoid shell-escaping.
- **Business-discovery query** — write raw QL; the `maps` skill's `nearby` covers POI
  categories (restaurant, hospital, ...) but NOT business tags:
  `node/way["office"|"company"|"craft"|"shop"="computer"](around:6000,<lat>,<lon>)`.
  Geocode the city center first (Nominatim). OSM business coverage in Egyptian
  provincial cities is THIN (Shebin El Kom: only 2 tagged businesses total) —
  directories beat OSM here; use Overpass only as a cross-check.
- **web_extract tool is search-only on this box** (ddgs backend). Use the helper
  `~/.hermes/skills/research/hermes-web-search-stack/scripts/extract_url.py`.
  Layer-1 trafilatura extracts LinkedIn job pages fine; Facebook and JS-rendered sites
  return "no usable text" (layer-2 needs playwright, usually absent) — fall back to
  web_search snippets for those.
- **Arabic URL slugs in curl/extract** trigger the security scanner (non-ASCII flag) —
  expected and auto-approved; don't "fix" the URL.
- Job boards (wuzzuf, forasna, bayt, tanqeeb) list local software houses — search
  city + role in Arabic; many small-house jobs never reach LinkedIn.
- Egyptian contact data: keep landline (`048-` prefix for Menoufia) and mobile together —
  phone is often the ONLY contact for small companies.

## References

- `references/shebin-el-kom-companies.md` — verified software/IT + data-adjacent org
  list for Shebin El Kom, Menoufia (2026-08 pass), incl. PIE & AI and Creativa Hub Menofia.
