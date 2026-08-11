---
name: study-abroad-scholarships
description: "Use when researching funded master's abroad for Egyptians."
---

# Study-Abroad Scholarship Research

Use when the user asks about studying abroad — funded master's, scholarships, grants, government programs — for themselves or via a source they share (e.g. an X post from someone asking about AI master's abroad). Built around Hesham's profile: Egyptian, Data Engineering grad June 2026, targets 2027 entry.

## Core workflow
1. **Extract the actual ask first.** If the trigger is an X/Twitter post, extract with `hermes-web-search-stack`'s `scripts/extract_url.py` (works on x.com URLs, no xurl/auth needed — web_extract tool alone errors with ddgs's search-only backend). The tweet is often Arabic — read it before researching.
2. **Nail the timeline FIRST.** The user's graduation date determines the target intake: grad June 2026 → target 2027 entry → applications open **fall 2026**. Grad 2027 → 2028 entry. Everything below depends on this.
3. **Map each program to its APPLICATION window, not its name.** "2026-2027" in a program name ≠ when you apply. Erasmus Mundus 2027 entry: per-program deadlines Oct 2026–Jan 2027. Sweden SI 2026/27: university apps due mid-Jan 2026, SI portal Feb 9–25 2026.
4. **Verify every deadline on the OFFICIAL source** (studyinnl.org, si.se, daad.de, investyourtalentapplication.esteri.it, campusfrance.org, vliruos.be, erasmus-plus.ec.europa.eu). Aggregators (scholars4dev, scholarshipscorner, opportunitiesforyouth, globaladmissions) carry stale or conflicting dates — use them for discovery, never for a quoted deadline.
5. **Rank by funding × fit × acceptance odds.** Fully-funded ≠ best odds: Erasmus Mundus ~1–5% acceptance; Stipendium Hungaricum has dedicated Egyptian slots via bilateral agreement and is far more realistic.
6. **Factor post-study work rights** into the ranking — for Hesham (Data Engineer) job outcomes matter as much as the scholarship: NL Orientation Year visa (1 yr job hunt → highly-skilled migrant), Germany 18-month job-seeker, Sweden 12 months.
7. **Deliver a ranked shortlist** with per-program: funding, application window, the catch, official URL. Offer a next step (application calendar / SOP template) rather than stopping at the list.

## Verified catalog (pass of 2026-08-11, Egypt-based students)
See `references/europe-catalog.md` for the full program-by-program detail: funding amounts, application windows, official URLs, and a timeline shape for 2027 entry. Re-verify deadlines before quoting — cycles shift yearly.

## One-shot session workflow
See `references/one-shot-workflow.md`: the batch-search sequence that delivered a full answer in one pass (Twitter-post trigger → parallel searches → verification batch → ranked shortlist), including the exact extraction command for x.com posts.

## Pitfalls
- **Aggregator blogs lie about dates** — always confirm on the official domain before quoting a deadline in chat.
- **Fulbright is country-specific**: Fulbright Egypt is a separate program with Egypt-dedicated slots (application ~May–June), not the US general program.
- **Turkey community consensus** (from the original thread): poor supervision reputation, near-impossible employment for non-Turkish speakers — treat as real-world signal, verify per-case.
- **Germany's real offer is tuition-free**, not a scholarship: public master's ~€0 tuition + blocked account (€11,904/yr) + 140 legal work days/yr. Don't frame Germany as "scholarship only."
- **NL Scholarship (€5k) covers a fraction of €15–20k tuition** — NL is a job-outcome play (ASML, Booking, NXP, Philips), not a free ride; pair with university scholarships (Twente €3k–22k/yr, TU Delft van Effen full, Amsterdam Merit).
- **Erasmus Mundus is the community's top mention but worst odds** — always pair it with a realistic second track in the same shortlist.
