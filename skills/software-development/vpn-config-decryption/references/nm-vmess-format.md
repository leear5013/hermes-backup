# nm-vmess:// — NetMod's encrypted share-link format

Status: **CRACKED — keys extracted from the shipping APK** (2026-08-08, NetMod 4.2.0.635).
The decryption lives in the Go native lib (`libgojni.so`), NOT the dex. Three hardcoded
16-byte keys, payload split into 3 chunks, AES-128-ECB + PKCS#7 per chunk. End-to-end
decrypt of the user's 272-byte sample was in progress at session end (chunk order not
yet verified). See **netmod-3key-scheme.md** for the full chain + the three key literals;
do not claim a working decryptor until real JSON comes out.

## What we know for sure

- `nm-vmess://` is NetMod's own import scheme (the `nm-` prefix is NetMod's, not NPV's — user correction).
- **Some payloads are base64 of plain JSON (same as vmess); SOME ARE ENCRYPTED.**
  The user pasted a real sample that the naive base64-JSON path failed on:
  `❌ nm-vmess:// decode failed (UnicodeDecodeError): 'utf-8' codec can't decode byte 0xab`.

## Real encrypted sample anatomy (verified)

- Payload length after base64: **272 bytes = exactly 17 × 16-byte AES blocks** (no padding residue → full-block cipher like AES-CBC/CTR, or PKCS#7 padded data).
- First bytes hex: `ab 8f 2d 55 dd 1e 86 ec d9 cc 90 0e 18 f9 4e d0` — high entropy, no magic header, no JSON.
- Fails UTF-8 decode at byte 0 (0xAB) → not text, not base64-of-text.

## Detection recipe (put this in the bot, not a crash)

```python
raw = base64.b64decode(payload + "=" * (-len(payload) % 4))
if raw[:1] in (b"{", b"\xef"):   # '{' or UTF-8 BOM → JSON path
    d = json.loads(raw)
    print(json.dumps(d, indent=2))
else:
    # encrypted/binary — length % 16 == 0 is the AES-block fingerprint
    print(f"nm-vmess encrypted payload: {len(raw)} bytes (mod16={len(raw)%16}), first byte 0x{raw[0]:02x}")
```

## Tested key candidate — devkaj/telegram-vpn-decrypt-bot (VERIFIED FAIL for current format)

Source fetched 2026-08-08 (`git clone --depth 1 https://github.com/devkaj/telegram-vpn-decrypt-bot`).
It's a PHP Telegram bot (bot.php + api/NetMod + api/SlipNet) that decrypts NetMod and SlipNet configs.

- `api/NetMod/index.php` (Author Abolfazl Kaj @AbolfazlKaj, t.me/IRA_Team):
  ```php
  function DecryptNetM($a) {
      $key = '_netsyna_netmod_';
      $data = base64_decode($a);
      $decr = openssl_decrypt($data, "AES-128-ECB", $key, OPENSSL_RAW_DATA);
      ...
  }
  // then: preg_match('#^nm-([a-z]+)://#', $text, $m); $type = $m[1];  // vmess/vless/trojan...
  // strip prefix, decrypt, json_decode; if array → normal_link = $type."://".base64_encode($decrypted)
  ```
- Python test with pycryptodome on the user's REAL sample:
  ```python
  from Crypto.Cipher import AES
  key = b'_netsyna_netmod_'
  dec = AES.new(key, AES.MODE_ECB).decrypt(base64.b64decode(payload))
  # → b"m(\xc5\xd6;He>\xb2,..." garbage, NOT JSON
  ```
- **Conclusion: `_netsyna_netmod_` + AES-128-ECB does NOT decrypt the user's current-version
  sample.** It may work for older NetMod configs (the devkaj bot's market) — but current NetMod
  has a different key or cipher mode.

## SlipNet decryptor (same repo — useful pattern reference)

`api/SlipNet/index.php` `decryptData()`:
- `slipnet-enc://` prefix; format: `base64( 1 marker byte + 12-byte IV + ciphertext + 16-byte GCM tag )`
- Key: `hex2bin('214f052025b2f949605a5429ec3d5fa80c2022c168ad946e68852d447214dbd3')` (AES-256-GCM)
- Plaintext = pipe-delimited profile: `version|tunnel_type|name|domain|resolvers|authoritative_mode|keepalive|congestion|tcp_port|tcp_host|...`
- Takeaway: this author ships REAL working decryptors with hardcoded keys — so the NetMod key
  genuinely comes from the app. If a newer key exists, it's inside the current NetMod APK.

## APK-source hunt — completed dead-ends (verified 2026-08-08, do NOT re-probe)

Goal was a current NetMod APK to decompile for the key. All of these were tried and failed:

- **netmodvpnclient.com** — WordPress site. The "Download" menu link is a dead `href="#"`;
  the "Download NetMod for Android and Windows" button is JS-driven, NO direct .apk/.zip/.exe
  URL anywhere in the HTML (grep'd hrefs, data-*, buttons, all pages). `wp-sitemap.xml` returns
  only the homepage; `?page_id=360` is empty of links. **Skip HTML scraping of this site.**
- **APKPure** (`apkpure.com/search?q=netmod`) — Cloudflare challenge wall (`__cf_chl_tk`),
  and `apkpure.net` + `apkpure.com/.../versions` return **403** from this VPS.
- **Appteka** (`appteka.store/app/12br194052`) — page loads but `/apps/12br194052/download`
  returns an HTML JS shell (87KB), NOT the APK. Serve'd a Next.js page, no binary.
- **PGYER** (`pgyer.com/apk/apk/com.netmod.syna/download`) — empty response (blocked).
- **Wayback Machine** — `web.archive.org/cdx/search/cdx?url=netmodvpnclient.com*` returns
  `[]` (never archived). No APK recovery there.
- **GitHub `search/repositories?q=netmod+apk`** — only unrelated "Netflix Mod" hits.
- **t.me/s/<handle> previews** — all of netmod/netmodvpn/netmodsyna/netmod_syna/
  netmodvpnclient/NetModSyna return nothing; the real channel is **t.me/netmod_vpn_channel**
  (found via ddgs query "netmod vpn telegram channel official t.me", not by guessing).
- Key-variant guessing (9 keys × ECB/CBC + SlipNet GCM layout) — all garbage. Don't re-run
  these guesses; key must come from the app itself.

## Open leads (next steps when the user asks again)

**APK HUNT: COMPLETED 2026-08-08 — the current NetMod 4.2.0 (vc=635) APK was
downloaded from apkcombo and dex-scanned.** Working mirror chain + scanner details
in references/apk-hunting.md; re-runnable scanner in scripts/scan-dex-strings.py.

DEX scan findings (classes2.dex, NetMod 4.2.0.635, verified this round):
- `nm-vmess://` IS in the app — the import scheme is parsed in app code, and the
  scheme family regex is: `(vmess|vless|trojan|trojan-go|socks|ssh|ss|ssr|dns|wireguard|nm-xray-json)://`
  plus `nm-dns:// nm-http:// nm-socks:// nm-ss:// nm-ssh://` — i.e. `nm-` prefixes any
  protocol, and the value after `nm-<proto>://` is the (possibly encrypted) blob.
- `AESSettingsCipherMode` string → NetMod exposes an AES cipher-mode setting for
  configs; the cipher may be user-selectable (explains why the static devkaj key fails).
- `Lnetmodcore/Netmodcore;` + `Lgo/netmodcore/gojni/R;` → the crypto core is a **Go
  native bridge (gojni)**. The real key/mode lives in native libs, NOT the dex —
  next step: extract `config.armeabi_v7a.apk` from the XAPK and scan the `.so`
  (Go string data like `_netsyna_netmod_` would appear as plain bytes).
- SQLCipher (`net/zetetic/database/sqlcipher/*`) is used for the local DB (Room
  models: AppsModel, ServerGroupModel, V2RayModel) — that's the "private config"
  storage layer, distinct from the share-link crypto.

Remaining work (not yet done):
0. **MOSTLY DONE — see netmod-3key-scheme.md**: the 3 keys are extracted from
   libgojni.so (base64 literals `<n3t5yn^Nn3tm0d>`, `_netsyna_netmod_`,
   `nicetrybuddygoon`). The remaining step is verifying chunk-split order on the
   user's real 272-byte payload and wiring the decryptor into the bot.
1. ~~Extract native .so from `config.armeabi_v7a.apk` and scan for the key~~ — DONE,
   keys found. Go pclntab walker: scripts/go-pclntab-symbols.py.
2. Test candidate keys against the preserved 272-byte ciphertext (user's real
   sample, in chat history): AES-128-ECB/CBC first, then GCM (SlipNet layout as reference).
3. If the key is per-user or derived at import time (look for `SecretKeySpec` +
   password/derivation inputs near the decrypt call), the bot needs the same
   derivation — check `lockConfig`/password semantics in the dex.
4. Key-candidate finding technique that WORKS (used for `_netsyna_netmod_`): search GitHub for
   existing VPN-decrypt projects (`api.github.com/search/repositories?q=<app>+vpn`), clone the
   repo, and read the PHP/Python decrypt handlers — devkaj/telegram-vpn-decrypt-bot had a
   dedicated `api/NetMod/index.php`. The same trick applies to any future app: find the community
   decryptor first, then verify against the real sample.

## Pitfalls

- Do NOT claim "decrypted" for these — say plainly: encrypted format, key not yet found for current version.
- Do NOT invent a schema. State the AES-block fingerprint as evidence, not the solution.
- GitHub code search requires auth; grep.app is Vercel-walled; phcorner is login-walled —
  use `api.github.com/search/repositories` (no auth) + raw file fetches instead.
