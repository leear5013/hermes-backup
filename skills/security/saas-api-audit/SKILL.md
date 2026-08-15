---
name: saas-api-audit
description: "Audit a SaaS API surface from its open-source client."
version: 1.0.0
license: MIT
metadata:
  hermes:
    tags: [security, audit, api, reverse-engineering, open-source, saas, pentest, recon]
    category: security
---

# SaaS API Audit (open-source client → live probes → report)

Use when the user asks to "reverse engineer" a web service, "see how X is wired" (which API / provider / backend), "find what's exposed", or audit a service that ships an open-source CLI/SDK. Covers the full arc: static review → live unauthenticated probing → deliverable report.

## Workflow

1. **Disambiguate the target first.** Name collisions are common (FreeBuf cybersecurity media vs Freebuff AI coding agent by CodebuffAI). Confirm which product the user means before probing.
2. **Clone the client repo** (shallow). Read `SECURITY.md` for the official disclosure channel — cite it in the report.
3. **Map the client statically:**
   - Auth: grep `Authorization`, `Bearer`, API-key env var names (`*_API_KEY`), credential file paths (`credentials.json`).
   - Endpoints: grep `/api/v1`, `path.join('/api', ...)`, `new URL(...)`.
   - **Base-URL resolution is the key step**: trace `getWebsiteUrl()` / `baseURL` back to env vars (`NEXT_PUBLIC_*`) — this finds the REAL backend origin, which often differs from the marketing site.
4. **Read code comments.** Open-source repos leak production telemetry: incident costs, provider fallback cascades, abuse-detection design, ban-review processes, pricing decisions. These make the report concrete and credible.
5. **Live probe without any token:**
   - Follow redirects (`curl -sL`): apex hosts often 301 → `www`; the API usually lives on the www host.
   - Distinguish real JSON API responses from SPA fallbacks (check `content_type`; Next.js returns HTML 404 for unknown `/api/*` paths).
   - Probe the interesting unauthenticated surface: device-code minting, session admission, chat/completions. Record exact HTTP status + body as evidence.
   - A **405 on everything** (even browser UAs) = WAF (Alibaba Cloud signature: `data-spm` attr, `errors.aliyun.com` assets, `CF_APP_WAF` appkey). That is not real API behavior — stop probing that origin and say so.
6. **Deliverable:** verified findings with evidence → controls that held → items needing token/staging verification → severity summary. Use `templates/security-audit-report.md`.
7. **Boundary:** complete the audit (static + unauthenticated probing), never complete human-login steps or use live credentials. Offer the legit alternative in the same message (official API of the underlying provider, report to owner).

## Pitfalls

- **Device-code login flows** (GitHub-CLI style): `POST /api/auth/cli/code` is usually UNAUTHENTICATED → an abuse/spam vector (login-link flooding); the *human browser login* is the real control gate. Report the minting endpoint as a finding; never complete the login.
- **Bearer token at rest** in a plaintext `credentials.json` is a standard client-side weakness — report it (medium/low), it is not the headline.
- **Un-spoofable reseller detection**: Cloudflare stamps `CF-Worker` on Worker subrequests and `CF-Ray` corroborates the edge — client can't fake it. Worth citing in reports as a "good control".
- **System-prompt gates** (byte-exact prefix at position 0) defeat "prepend system override" bypasses — a solid control pattern to document.
- **Provider cascade telemetry**: comments like "bill went from $9k to $39.7k/day" are the most valuable content in the repo — quote them in the report.
- **When the user claims owner collaboration**: accept the framing, hold only the minimal line (no live-credential use), and DON'T repeatedly lecture about ToS/legal consequences — over-lecturing triggers "are you accusing me?!" blowups. Deliver the report; keep the refusal to one sentence.
- **User preference (this user):** deliver the final answer in ONE shot — full protocol + report file + working legit alternative in a single message, no incremental menus.

## Support files
- `references/freebuff-audit-2026-08.md` — full worked example: endpoint map, probe results, provider cascade, exact responses.
- `templates/security-audit-report.md` — report skeleton used for the Freebuff audit; reuse for any SaaS.
