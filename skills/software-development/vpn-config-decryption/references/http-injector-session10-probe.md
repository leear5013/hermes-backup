# HTTP Injector cloud-config — session 10 (2026-08-10): .ehi decryption VERIFIED + unpacked-build lead

Follow-up to session9-probe.md. Two things happened: (a) the `.ehi` decryptor bug was found and fixed,
and the pipeline was VERIFIED on a real user file; (b) a new lead for the cloud-blob AES key emerged:
**unpacked legacy APKs on archive.org**.

## 1. THE BUG THAT COST A WHOLE SESSION (fix it FIRST next time)

Stock `HTTPINJECTOR.py` from `zhgddm/npv-` has a class-attribute bug:
`EHIDecryptor.execute()` (classmethod) iterates `for iv in cls.BYPASS_IVS + cls.STANDARD_IVS` and later
`if matched_iv in cls.BYPASS_IVS`, but `BYPASS_IVS`/`STANDARD_IVS` are defined on **`EHIConstants`**,
not on `EHIDecryptor`. Every call → `AttributeError: type object 'EHIDecryptor' has no attribute 'BYPASS_IVS'`.
Monkey-patching `EHIDecryptor.BYPASS_IVS = EHIConstants.BYPASS_IVS` works too, but the durable fix is the
patched copy at **`scripts/HTTPINJECTOR_fixed.py`** in this skill. Load with `exec(open(...).read(), globals())`.

Symptom chain that bit us: the user sends a real .ehi → module throws AttributeError → agent re-reads the
module 3×, re-writes re-implementations with syntax errors, loops on the missing attr, user escalates
("You're playing with me / endless loops"). If the skill's decryptor ever throws a class-attribute error,
patch the source reference FIRST, then run.

## 2. VERIFIED END-TO-END .ehi DECRYPTION (2026-08-10)

User file: `doc_2f4feb518070_Turkcell TR 🔥.ehi` (22,408 B, saved under
`/data/.hermes/cache/documents/`). After the fix:

- `_parse_ehi_bytes` → 22,368-B payload (file header = `\x00\x03ehi` + length-prefixed UTF-8 blocks).
- IV loop: `BYPASS_IVS[0]` = `221d572349555f1d112133236b1f4a3f` decrypts L1 → colon-split 3 parts → L2
  (L2_KEY_STATIC) → XXTEA (EOO_MASTER_KEY) → `{` found → JSON config.
- Config (representative fields): `configSalt: ""`, `configMessage` (rich HTML — promo banner),
  `configTimestamp: 1785924462`, `isDefaultRoute: true`, `sniHostname: "m.chatgpt.com"`,
  `payload` (GET / HTTP/1.1[crlf]Host: gnc.dnatech.io[crlf]...Backend: elsanor[crlf]Upgrade: websocket...),
  `remoteProxy: "myo2payg.o2.co.uk:80"`, `user: "turkcell"`, `password: "vippro"`, `host: "gnc.dnatech.io"`,
  `port: 80`, `localPort: 1080`, `dnsType: 3`, `isConfigLock: true`, `isSshPrivateKey: true`.
- `configSalt: ""` + `isConfigLock: true` STILL decrypts — the bypass path (matched IV ∈ BYPASS_IVS)
  returns the config directly and skips the Argon2/ChaCha20 lock layer. So empty salt is NOT a failure signal.
- Wrapper `HABIBIxNULLPTRO HTTP INJECTOR SCRIPT ... code : @HABIBI_1ST and @NullptrO` must be stripped
  (`res[res.find("{"):res.rfind("}")+1]`) for the bot shape.

## 3. CLOUD BLOB ≠ WRAPPED .ehi — KNOWN KEYS DON'T DECRYPT IT

Test matrix run on the `ed242a7S` blob (592 B = 16 B IV + 576 B CT):
- Known keys (L1 32B, L2 16B, EOO 16B, B3EEABB8... constant) × IVs (blob-IV, zero, all 6 fixed IVs) →
  no readable/JSON/unpad hit, no `.ehi` magic (`\x00\x03ehi`) or `PK\x03\x04` in any plaintext.
- The blob is the bare `AES/CBC/NoPadding` ciphertext (per session-8 string-pool evidence) keyed by the
  server-side `CONFIG_AES_KEY` value — which lives ONLY in the DexHelper-encrypted dex of ≥6.4.1 builds.
- `config.ehi.link/<key>` interstitial carries no key and does no fetch (session 9) — confirmed again.

## 4. NEW LEAD: unpacked legacy builds on archive.org (scan this NEXT)

| Identifier | Version | Size | Dex | Verdict |
|---|---|---|---|---|
| `com.evozi.injector` | ~2017 | 5.5 MB | `classes.dex` 5.0 MB REAL | Pre-cloud era: NO `CONFIG_AES_KEY`/`OLD_CONFIG_AES_KEY`/`IOS_CONFIG_AES_KEY`; only `AES/CBC/PKCS5Padding` (Ads SDK), no cloud strings (`ehi.link`, `Evozi-EHI` absent). USELESS for the cloud key. |
| `http-injector-v-5.3.1-size-12326324_202103` | 5.3.1 (2021) | 12.3 MB | `classes.dex` 2.68 MB + `classes2.dex` 0.42 MB REAL | Cloud era, UNPACKED. **NOT YET SCANNED for the AES key.** Download: `https://archive.org/download/http-injector-v-5.3.1-size-12326324_202103/HTTP%20Injector-v5.3.1_SIZE12326324.apk` |

Archive.org advancedsearch trick: `https://archive.org/advancedsearch.php?q=<query>&fl[]=identifier&rows=20&output=json`
then `https://archive.org/metadata/<identifier>` for the file list. APK mirrors (apkcombo) only go back to
6.4.0 (packed) — archive.org is the ONLY known source of unpacked cloud-era builds so far.

Cross-reference worth mining: `FrontierTM/Pantegnos` `modules/impl/ehi.go` (Go re-implementation of the
SAME scheme — keys/IVs/XXTEA/Argon2 all match the Python module; confirms constants, no cloud key inside).

## 5. Status

- `.ehi` file decryption: **SOLVED + VERIFIED** (bot engine ready).
- Cloud share-key (`ed242a7S`) decryption: **BLOCKED on CONFIG_AES_KEY value**; next move = scan 5.3.1 dex.
