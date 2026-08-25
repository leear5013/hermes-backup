# Google Dorks quick-reference (verification-safe)

## People
- "full name" -site:linkedin.com
- "full name" "city" OR "university" OR "company"
- intitle:"full name" (facebook OR instagram OR twitter)
- "email@domain" -site:domain.com (footprints elsewhere)
- "0x..." (crypto wallet in public profile)

## Email / username
- "username" site:github.com
- "username" site:reddit.com (RSS-first via reddit skill)
- "username" "joined" (profile strings)
- inurl:"user/username" (profile URLs)

## Domains / infra
- site:domain.com -www (subdomains via search)
- intitle:"index of" "domain.com" (open dirs — informational only)
- "domain.com" filetype:pdf (documents with metadata)
- inurl:admin site:domain.com (surface only — no exploitation)

## Companies
- "company name" "director" OR "founder" OR "owner"
- "company name" site:linkedin.com/in (profiles)
- "company name" "whatsapp" OR "telegram" (support channels)

## Verification notes
- Dorks surface candidate sources; every finding must be verified
  at the primary source before it becomes evidence.
- No dorking for credential dumping, exploitation, or bypass.
- Use archive.org snapshots when pages are volatile.
