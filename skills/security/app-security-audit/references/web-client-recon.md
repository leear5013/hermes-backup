# Web client / browser-game recon (validated on FrontWars vs OpenFront, 2026-08-21)

## Bundle acquisition

```bash
curl -sL -A "Mozilla/5.0 ... Chrome/120" https://site.io/ -o page.html
grep -oE 'src="[^"]*\.js[^"]*"' page.html        # module bundle URLs
curl -sL "<bundle-url>" -o bundle.js             # often 2MB+ single file
```
Cloudflare-protected sites (openfront.io 403'd plain curl): add full browser
headers (UA + Accept + Accept-Language). If still 403, get the bundle from a
portal mirror (CrazyGames embed) or the public GitHub repo instead.

## Fork detection (is site X a re-skin of known project Y?)

1. Download both bundles. Compare sizes and count signature identifiers
   (unique game/engine strings, class names like `MIRVWarhead`,
   `defendedBorderColors`, `terraNullius`). Shared signatures = same codebase.
2. Diff feature markers: routes (`/auth/*`, `/api/*`), SDK refs
   (turnstile/captcha count!), platform SDKs (CrazyGames/Poki/Steam/Discord).
3. If upstream is open-source: read its server code on GitHub — the fork's
   server logic is largely public knowledge. Upstream security comments
   (e.g. JoinVerify.ts Turnstile-bypass notes) tell you exactly what the fork
   may have dropped.

## API surface enumeration from a minified bundle

```python
routes = set(re.findall(r'[`"\'](?:/(?:api|auth|users)[^`"\'\s]{0,50})[`"\']', js))
socket_types = set(re.findall(r'send\(\{type:`([a-zA-Z_]+)`', js))     # client→server msgs
intent_names = set(re.findall(r'[`"\'](attack|nuke|donate_gold|...) [`"\']', js))
auth_flow    = re.findall(r'fetch\(`?[^`]*?(/auth/[^`]*)`?', js)
admin_bits   = [m for m in ['x-admin-key','ADMIN_TOKEN','dummy-admin-token'] if m in js]
```
Config-schema defaults in client bundles (`dummy-admin-token`, header names)
are recon gold — they name exactly what to check server-side.

## Probing etiquette (authorized-audit standard)

- Unauthenticated GET only; one probe per endpoint; note HTTP code + body head.
- `/api/game/<id>/route`-style endpoints: use obviously-invalid IDs ("test").
- Never join live game servers, never send intents — that disrupts real players.
- Captcha absence in the client = bot-abuse surface worth reporting, but say so
  as analysis, not by farming their lobbies to prove it.

## Worked example findings (FrontWars)

- Zero `turnstile` refs vs upstream's 25 → no human verification on join;
  auth falls back to self-generated localStorage UUID (`persistent_id`).
- `dummy-admin-token` default + `x-admin-key` header name shipped client-side.
- Fork-only features (parties/invite codes, clan tags, Discord Activity auth
  via `/api/auth/discord-activity`) = extra attack surface upstream lacks.
