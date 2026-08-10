# HTTP Injector Cloud Config API — Confirmed Endpoint (2026-08-10)

## Verified via direct probing with correct headers

- **Host**: `www.ehiapp.com`  
  (Note: `ehiapp.com` apex returns 301 → `www.ehiapp.com`; probing `www.ehiapp.com` directly avoids redirect loop)
- **Required header**: `X-Platform: android`  
  (Without this, POST returns 401 `{"status":401,"error":"Missing required security headers","code":401}`)
- **Endpoint**: `POST /httpinjector/config`
- **Request body**: JSON containing the share key, e.g., `{"key":"ed242a7S"}`
- **Response**: `{"code":200,"data":"<base64-encoded AES-CBC blob>"}` where:
  - First 16 bytes of decoded blob = IV (random per request)
  - Remainder = ciphertext (AES-128/CBC/NoPadding)
- **Encryption**: Static AES key embedded in the app (DexHelper-encrypted payload); not recoverable via static string scan
- **Other notes**:
  - `GET /httpinjector/config` → 405 (method not allowed) — Cloudflare edge block
  - `PUT/PATCH/DELETE/OPTIONS` → 301 → `www.ehiapp.com` (then WAF 403)
  - `GET /httpinjector/login` and `/iap/verification` → 404 JSON `{"error":"Not found"}` (proves real JSON backend behind Cloudflare)

This endpoint is the live cloud config fetcher used by the app after resolving `config.ehi.link/<key>` → deep link → `ConfigImportActivity`.
