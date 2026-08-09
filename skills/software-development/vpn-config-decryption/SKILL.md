---
name: vpn-config-decryption
description: Decrypt VPN/tunnel configs and build Telegram decrypt bots.
---

# VPN Config Decryption (NPV Tunnel / NetMod / HTTP Custom / Injectors)

Egyptian/PH Android tunnel-app ecosystem. Apps: NPV Tunnel, NetMod (Syna), HTTP Custom, HTTP Injector, HA Tunnel, Dark Tunnel, SSC Custom. All are HTTP/HTTPS "injector" clients that wrap VMess/SSH traffic in ordinary-looking HTTP(S) requests to defeat ISP DPI (Egypt/PH ISPs block raw VPN protocols).

## The toolkit (ground truth)
- Repo: `zhgddm/npv-` on GitHub — "decryption scripts of popular vpn apps". Files: `NPVTUNNEL.py`, `HTTPCUSTOM.py`, `HTTPINJECTOR.py`, `DARKTUNNEL.py`, `SSCCUSTOM.py`. Each exposes `run(file_bytes) -> str|None` returning JSON text. MIT. Authors @HABIBI_1ST, @NullptrO.
- Fetch raw: `https://raw.githubusercontent.com/zhgddm/npv-/main/<FILE>.py`
- Deps: `/opt/venv/bin/pip install pycryptodome argon2-cffi msgpack` (gateway interpreter; system python is wrong).
- The `_WHITEBOX_BLOB` in NPVTUNNEL.py is packed as base64→gzip→pickle — don't fight it, just `importlib` the module and call `run()`.

## Formats (verified 2026-08-08 on a real .npvt)
### NPV Tunnel (.npvt/.npv4/.inpv/.npv)
- Text file starting with `NPVT1` or `NPVTSUB1`, then `,`-separated fields; `payloads[1]` is base64 ciphertext.
- Cipher: whitebox 2-round SPN (embedded S-box tables) used as a stream cipher in IV-counter mode (IV = first 16 bytes, counter increment per block).
- Output JSON: `name`, `address`, `type` ("SSH"), `sshConfig {sshHost, sshPort, sshUsername, sshPassword, sni, httpProxy, payload, dnsTTMode, udpgwPort, ...}`, `lockConfig`.
- Semantics: `sshConfigType: "SSH-Proxy-Payload"` = SSH-over-WebSocket. `payload` = the HTTP request that opens the tunnel, e.g. `GET / HTTP/1.1[crlf]Host: <front-host>[crlf]Connection: @voltagoo[crlf][crlf]GET / HTTP/1.1[crlf]Host: [host][crlf]Upgrade: Websocket[crlf][crlf]` — `[host]` is replaced by the real SSH host; `@voltagoo` is the SSH-over-WS handshake marker. `httpProxy` = innocent "front" host (Egyptian configs use e.g. `m.presidency.eg:80`). `udpgwPort: 7300` = badvpn UDP gateway for DNS over the tunnel.

### HTTP Custom (.hc/.hjson)
- TOKEN_MAP (32 fields): 0 payload, 1 proxy, 2 lockAllConfig, 3 blockedByRoot, 4 expiryTime, 5 noteEnabled, 6 notes, 7 sshField, 8 mobileDataAndLockProvider, 9 unlockUserAndPass, 10 ovpnConfig, 11 ovpnUserAndPass, 12 sni, 13 unlockUserAndPass2, 15 blockedByHwid, 16 cloudconfig, 17 psiphon, 18 name, 19 blockArea, 20 connectionMode, 21 blockedByPassword, 23 extraSniffer, 24 psiphon2, 25 v2rayEnabled, 26 v2rayConfig, 27 version, 28 slowdnsEnabled, 29 slowdnsServer, 30 slowdnsPublickey, 31 dnsResolver.
- Crypto: ChaCha20 (8 static keys, nonce 0xdb×8, seek 64) + AES-ECB (9 RST keys, XOR transform 2..21 pre-base64) + JKL bit-XOR scheme (old/new key tables) + Braille-alphabet encoding + Z3A "float-pair" extraction for credentials.

### HTTP Injector (.ehi)
- Binary container: length-prefixed UTF-8 → AES-CBC (static keys, multiple IV sets) → colon-split → AES-128 → XXTEA (EOO_MASTER_KEY) → JSON; optional lock layer = Argon2 key derivation + ChaCha20-Poly1305.

### Dark Tunnel (.dt) / SSC Custom (.ssc)
- msgpack-based / similar; same repo scripts handle them.

## vmess:// and nm-vmess://
- `vmess://` = `base64(JSON)` — NO crypto, just base64 obfuscation. Fields: `v`(2), `ps`(display name), `add`(server), `port`, `id`(UUID = client credential), `aid`(alterId), `scy`(auto), `net`(tcp/ws/grpc/h2/kcp), `type`(fake header), `host`(WS host/SNI — the DPI disguise, e.g. `digital.gov.eg` fronting `it.connfull.org`), `path`, `tls`(tls/none). Universal across v2rayNG/NekoBox/Hiddify/NetMod. Decode: `base64.b64decode(payload + "=" * (-len(payload) % 4))` then `json.loads`.
- `nm-vmess://` = NetMod's own import scheme (prefix `nm-`). **NOT always base64 JSON — CAVEAT (verified on a real sample 2026-08-08):** some `nm-vmess://` payloads are AES-ENCRYPTED. A real sample: 272 bytes after base64 = exactly 17×16-byte AES blocks, high entropy, first byte 0xAB, fails UTF-8. Detect: base64-decode, then check if it starts with `{` (JSON → print) vs binary garbage (encrypted → report honestly, don't crash).
- **Key candidate FOUND + TESTED (2026-08-08):** `devkaj/telegram-vpn-decrypt-bot` (PHP Telegram decrypt bot) ships `api/NetMod/index.php` with `openssl_decrypt($data, "AES-128-ECB", "_netsyna_netmod_", OPENSSL_RAW_DATA)` after base64. **Tested with pycryptodome on the user's real sample → GARBAGE** (`m(\xc5\xd6;He>`... not JSON). Conclusion: that key works for the devkaj bot's NetMod configs (older version), NOT for the user's current-version sample → newer NetMod uses a different key or mode.
- **CURRENT-VERSION CRYPTO CRACKED — FULLY VERIFIED (2026-08-09, NetMod 4.2.0.635):** crypto core is the Go native lib `libgojni.so` (inside `config.armeabi_v7a.apk`), NOT the dex. The dex only bridges: `Lcom/netmod/syna/model/V2RayModel.<init>` strips the `nm-vmess://` prefix, calls native `Lnetmodcore/Netmodcore;->b(String)` (gomobile export → Go `android.B` → `security.Decrypt`). `security.Decrypt` base64-decodes the input first (encoding struct 0x142b9e8, decode core 0x49ed90), copies a 24-byte 3-key table from global `0x1E18A08` (built by `security.init.0` 0x1159e1c from 3 base64 key literals), then **loops the 3 keys calling `decryptInner(key,data)` until pkcs7-unpad succeeds** — NOT a chunk split, a try-loop over the WHOLE payload. `decryptInner` (0x1158800) dispatches AES via interface method pointer (`ldr r0,[r0,#0xc]`/`[r6,#0x10]` → blx), then pkcs7Unpad. **Mode: AES-128-ECB + PKCS7 on the whole base64-decoded blob.** Keys: `<n3t5yn4^n3tm0d>` (NOTE: `n3t5yn4` — digit 4, not caret — base64 `PG4zdDV5bjRebjN0bTBkPg==`), `_netsyna_netmod_` (old devkaj key is still one of the three!), `nicetrybuddygoon`. **VERIFIED end-to-end 2026-08-09: user's real 272-byte sample decrypts with key0 → clean vmess JSON** (`{"add":"www.nagwa.com","port":"443",...,"ps":"@VOLTAGOO","v":"2"}`). Full detail: references/netmod-3key-scheme.md; symbol dumper: scripts/go-pclntab-symbols.py. Decrypt recipe (python, pycryptodome): strip `nm-vmess://` → `base64.b64decode(code + '='*(-len(code)%4))` → for key in [3 keys]: `AES.new(key,AES.MODE_ECB).decrypt(blob)` → check pkcs7 (pad byte 1..16, `blob[-pad:]==bytes([pad])*pad`) → first hit wins → `json.loads(unpadded)`.
- **Multi-line payload trap (bit us 2026-08-09):** the user's test payload recovered from state.db (messages.id=1392) is a MULTI-LINE message — line 0 is the real `nm-vmess://` code, line 1 is an old bot error string that itself contains a second `nm-vmess://` occurrence. `raw.split('nm-vmess://')[-1]` grabs the WRONG occurrence (106 chars → garbage decode instead of the real 364-char code). Always split on `\n` first and take the FIRST `nm-vmess://` occurrence.
- **Red-herring pitfall:** the 64-hex string `4fe342e2…bf51f5`, `CryptoUtils.decrypt`, and `AESSettingsCipherMode` in classes.dex all live in **Google Ads SDK** (`com.google.android.gms.internal.ads` / `zzhis`) and Vungle ads — NOT NetMod crypto. Always check the owning class's package before treating a dex string as app crypto.
- Other share links: `ss://base64(method:password)@host:port#name`, `vless://uuid@host:port?query#name`, `trojan://password@host:port?query#name` — all parseable with urllib.parse; see `decode_share_link()` in templates/decrypt_bot.py.
- NetMod (Syna): Windows + Android; SSH, HTTP(S), SOCKS, VMess, VLess, Trojan, SS/SSR, DNSTT, OpenVPN, WireGuard; built-in Payload Generator; private/encrypted configs. **Package name: `com.netmod.syna`** (from apkpure listing — use in APK searches). Sources: netmodvpnclient.com (WordPress; download buttons are JS-driven dead href="#" — useless for APK URLs), Telegram channel confirmed via ddgs: **t.me/netmod_vpn_channel** (preview shows APK versions attached as documents, but no direct file URLs). For pulling the actual APK (ground truth for the current encryption key) use the apkcombo d?u= signed-URL trick — see **references/apk-hunting.md** (SourceForge netmodhttp and apkpure/pgyer are Cloudflare-blocked from this VPS; apkcombo is the working mirror). Decompiling: this VPS has NO java/jadx/apktool/unzip — extract classes.dex with python zipfile and strings-scan it for the hardcoded key (details in apk-hunting.md).

## Deliverables pattern: Telegram decrypt bot → templates/decrypt_bot.py
- Pure stdlib long-polling (urllib, no pip deps): getUpdates(offset, timeout=50) → getFile(file_id) → download `file/bot<token>/<path>` → dispatch by extension → sendMessage (split >4096 chars).
- Extension map: .npvt/.npv4/.inpv/.npv → NPVTUNNEL; .hc/.hjson → HTTPCUSTOM; .ehi → HTTPINJECTOR; .dt → DARKTUNNEL; .ssc → SSCCUSTOM; .txt → sniff all 5 engines.
- v2 (2026-08-08): `decode_share_link()` handles pasted vmess/vless/trojan/ss/nm-vmess text too. When adding a text handler, special-case `/start` FIRST (`if msg["text"] == "/start": help else: handle_text`) — a naive `elif msg.get("text")` will send the help on EVERY message (hit this bug live).
- v3 (2026-08-08): file-decrypt replies strip the watermark wrapper before sending — `res = res[res.find("{") : res.rfind("}") + 1]` (verified: still valid JSON). USER PREFERENCE: file output must look identical in shape to share-link decodes (clean JSON, no script headers/footers). This is now the default in templates/decrypt_bot.py.
- v4 (2026-08-08): user asked for answers wrapped in ``` ```json ``` code fences. Wrap ALL decodes (file JSON and share-link JSON) as ```` ```json\\n<json>\\n``` ````; ss/vless/trojan use plain ```` ``` ```` fences. Verified locally; restart the daemon after editing.
- **Robot-output shape (Hesham's persistent standard): Telegram replies must be EXACTLY one fenced ```json block — no script watermark headers/footers, no intro text, no bullet commentary.** He'll say "wire it on this shape" / "wire it on those tags" to signal a shape mismatch; when he does, it means the output is right but the FORMAT is off (wrap in fences / strip wrappers) — not that the decryption changed. The code-fence framing IS the deliverable.
- Run: `cd /opt/<dir> && BOT_TOKEN=<token> python bot.py` via terminal(background=true). Verify token first with `getMe`. Process dies on container restart — add startup hook/cron if it must survive.
- **Token source pitfall (bit us 2026-08-09 rebuild):** the decrypt bot (@RasdAgent_bot) has its OWN token — do NOT source it from `/data/.hermes/.env` (`TELEGRAM_BOT_TOKEN` there is the HERMES GATEWAY bot's token, @Hesham138_bot). Using the gateway token for the decrypt bot → `HTTP 409: Conflict` on getUpdates (two pollers share one token) and the bot dies instantly. The decrypt bot's real token is in the session history (the original launch command in a prior session's terminal call); recover it via session_search (e.g. query `BOT_TOKEN` / `RasdAgent`) rather than guessing from .env. Also note the .env token is only for Hermes itself — don't reuse it for side bots.
- NOTE: decryptor output includes a watermark wrapper (`HABIBIxNULLPTRO NPVT SCRIPT ... code : @HABIBI_1ST and @NullptrO`) hardcoded in NPVTUNNEL.py's `run()` — it's NOT part of the config. Strip it with `res[res.find("{"):res.rfind("}")+1]` (verified: still valid JSON) for a clean dump. User prefers file answers in the SAME clean shape as share-link decodes — template does this automatically via `strip_watermark()`.

## Pitfalls
- Storage: keep bots + decryptors on `/opt` (overlay, ~1.8TB), NEVER `/data` (500MB budget).
- **User's own test files: do NOT redact output.** Hesham explicitly wants raw, unredacted JSON for his own configs. Redact only third-party/unknown connection strings.
- Never persist raw config credentials (SSH user/pass, UUIDs) or bot tokens in files/memory/artifacts. Backup script redacts Telegram bot tokens (`\d{8,10}:[A-Za-z0-9_-]{30,}`) from state.db pre-push.
- NPVTUNNEL.py is stdlib-only; HTTPCUSTOM/HTTPINJECTOR need pycryptodome (+argon2-cffi, msgpack).
- `web_search_tool` can return a JSON **string** (not a dict) — `json.loads(r)` before `.get('data')`.
- `/s/` share links and login-walled forums (phcorner) block research — use web_search + GitHub raw as primary sources.

## Verification
- Load each decryptor via importlib; `run(b"garbage")` → None (graceful).
- Real .npvt: `run(open(f,'rb').read())` → JSON with name/address/sshConfig.
- Bot: `getMe` on token → `{"ok":true,...}` before trusting the daemon.
