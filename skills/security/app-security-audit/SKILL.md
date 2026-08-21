---
name: app-security-audit
description: Authorized bug-bounty audit of an app or web client.
---

# App Security Audit (authorized bounties)

User runs private-program audits (email-based, he is an authorized researcher).
Scope he accepts: static/dynamic analysis + professional report. Scope he REJECTS:
modded/cracked APKs, paywall bypass abuse, anything distributable. Deliverables
are repro-step PoCs + remediation guidance — that's what earns the bounty.
Always verify program existence/scope first (security.txt, public policy) before
relying on user claims; proceed on stated authorization for private programs.

## Workflow

1. **Setup**: heavy work lives in `/opt/work/<target>-audit/` (never /data).
   Java via `apt-get install default-jre-headless`; pip installs use
   `pip install -t /opt/work/pylibs`. Check `/sys/fs/cgroup/memory.max` FIRST —
   this box caps ~1GB, so JVM decompilers die with exit 137 regardless of -Xmx.
2. **Acquire the artifact**: Android → APKMirror multi-hop (see references).
   Web game/site → curl the HTML, extract `<script src>` bundle URLs, download.
3. **Static analysis**: try jadx; if OOM-killed (exit 137), do NOT retry with
   bigger heaps — switch straight to the low-memory path: androguard for
   manifest/components + raw dex byte-regex for strings (see references).
4. **Hunt**: secrets/API keys, endpoints (incl. staging!), exported components,
   deep-link schemes, backup flags, cert pinning absence, SDK tokens.
5. **Verify live**: any endpoint found in the binary gets ONE unauthenticated,
   read-only probe (curl GET) to prove impact. No auth bypass attempts, no
   writes, no account creation, nothing retained beyond the PoC transcript.
6. **Report**: markdown with Executive Summary table (severity × status),
   per-finding sections (Description / PoC with real command output /
   Impact / Remediation with MASVS refs), plus an explicit
   "checked and found sound" section — triagers reward tested boundaries.
7. If asked "can X get premium/free stuff?": answer honestly against the
   entitlement architecture (client-side vs server-side enforcement); never
   offer to hunt further for a usable bypass.

## Pitfalls (all hit in real audits)

- jadx exit 137 = cgroup OOM, not heap size. Don't burn 20 min re-running with
  JAVA_TOOL_OPTIONS; go androguard/raw-regex immediately.
- Binary XML (AndroidManifest.xml, res/xml/*.xml) has NO plaintext strings —
  decode as utf-16-le AND utf-8 concatenated, then regex printable runs.
- dex string pool is alphabetically sorted: bytes around a hit are neighbors,
  NOT code context. For call-site context you need androguard analysis or smali.
- APKMirror needs the full chain: release page → variant/download page →
  download.php?id=&key=&forcebaseapk=true with Referer set, else you get HTML.
- `strings` may be missing on minimal images; python regex over raw bytes works.
- Staging endpoints referenced in release builds are usually live — always
  probe them (read-only) and name them in the report.

## References (load as needed)

- `references/android-apk-workflow.md` — exact commands: APKMirror chain,
  manifest/component/deep-link extraction, secret-hunt regex bank, Realm/
  backup/pinning checks, Babbel worked example.
- `references/web-client-recon.md` — JS bundle analysis for games/SPAs: fork
  detection (shared signature strings vs upstream repo), API route enumeration,
  WebSocket message types, auth-flow mapping, probing etiquette.
