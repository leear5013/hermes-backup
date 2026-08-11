# SNI candidate selection for Egypt (quota-whitelist bypass) — 2026-08-11

## Context
Hesham's Egyptian ISP (Etisalat-style quota): at 100% data consumed, ALL traffic is
blocked EXCEPT whitelisted destinations (mostly .gov.eg portals). The vpnjantit
fake-SNI trick works there precisely because DPI reads the `sni=` label in the TLS
ClientHello BEFORE encryption — a whitelisted domain name in the SNI makes the whole
tunnel pass the filter at zero quota.

## Method (two levels)
1. **Server-side probe** (`scripts/sni_probe.py`): TLS handshake to the Railway TCP
   proxy (`*.proxy.rlwy.net:PORT`) presenting each candidate SNI (server must accept
   ANY SNI — it terminates TLS itself) + real-domain DNS/HTTPS liveness. This only
   builds the candidate pool; it cannot see the ISP filter.
2. **Client-side test** (`templates/sni_test_termux.sh`): run from the Egyptian
   connection at 0% quota in Termux. PASS on TEST-1 handshake = DPI let that SNI
   through → swap it into the vless link.

## Full results (all 36 domains, server-side 2026-08-11)
All 36 completed TLS 1.3 handshakes to sakura.proxy.rlwy.net:14210 (server accepts
any SNI). Liveness screening split them:

### Fully live (HTTP 200) — best camouflage ✅
egfwd.com · elpai.idsc.gov.eg · emis.gov.eg · eservice.incometax.gov.eg ·
islamic-council.net · maharatech.gov.eg · **mcit.gov.eg** · moa.gov.eg ·
mof.gov.eg · mohesr.gov.eg · scu.eg · traffic.moi.gov.eg · www.capmas.gov.eg ·
www.civilaviation.gov.eg · www.dar-alifta.org · www.egyptconsulates.org ·
www.emys.gov.eg · www.gafi.gov.eg · www.idsc.gov.eg · www.investinegypt.gov.eg ·
www.mlzamty.com · www.parliament.gov.eg

Top picks (natural traffic for a tech-student profile): **mcit.gov.eg** (Ministry of
Communications & IT — #1), www.parliament.gov.eg, www.gafi.gov.eg, scu.eg,
www.capmas.gov.eg, mof.gov.eg, traffic.moi.gov.eg.

### Live but weaker (403/405/timeout/broken cert) ⚠️
- Broken/expired real certs (cert verify failed — suspicious + risky): www.mod.gov.eg,
  www.manpower.gov.eg, psm.gov.eg, www.moc.gov.eg, www.mohp.gov.eg
- Timeouts (server exists but slow/dead — weak camo): digital.gov.eg, ekb.eg,
  enationality.moi.gov.eg, mped.gov.eg, www.nccm.gov.eg
- 403/405 (blocks probing): speedtest.net, moe.gov.eg, ar.awkafonline.com, www.nagwa.com
- Connection refused: www.moee.gov.eg

## Link mechanics after an SNI swap
Changing `sni=` invalidates any old cert pin. Options:
- Keep it simple: `allowInsecure=1&fp=chrome` (uTLS fingerprint param `fp=` is for
  ClientHello style, NOT hashes — hex in `fp=` = "unsupported fingerprint" on iOS cores).
- Or re-pin: sha256 of server cert, strip colons, uppercase → `pcs=<hex>` (Xray ≥26,
  new v2rayNG).
- Rule from the allowed-insecure deprecation: phone apps with old cores accept
  `allowInsecure=1`; Xray-core ≥26 CLI needs `pinnedPeerCertSha256` in JSON.

## Re-testing
ISP whitelists change. If the chosen SNI stops working, re-run the Termux script at
0% quota with an updated domain list and swap. Keep the candidate list mostly .gov.eg
— foreign domains (Google/CDN) are weaker camo under a strict whitelist.