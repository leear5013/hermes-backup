# SaaS API Surface & Abuse-Vector Audit Report

Template: fill in per audit. **Date / Scope / Method** first — method must state that only unauthenticated probing was used, no live credentials.

---

# <Product> API Surface & Abuse-Vector Audit
**Date:** YYYY-MM-DD
**Scope:** <domains / repo>
**Method:** Static code review of <client repo> + live unauthenticated probing. No account token used; no abuse of paid capacity.

## 1. Verified live findings
### F1 — <title> (SEVERITY — type)
`<method> <url>` → **<HTTP status>** `<body snippet>`
- <evidence / impact / recommendation>

### F2 — <title> (GOOD/INFO)
... (prove the gates that held — these make the audit credible)

## 2. Controls confirmed from source (working as intended)
| Control | Source | Effect |
|---|---|---|
| <name> | <file:line> | <what it stops> |

## 3. Findings needing owner-side verification (need token/staging)
- **<item>** — why it matters / what to test on staging / severity if confirmed

## 4. Bottom line
<2-4 sentences: what is exposed, what held, the ONE actionable item.>

**Severity summary:** F1 MEDIUM (rate-limit it), §3 item 1 HIGH-if-confirmed (verify), item 3 LOW.
