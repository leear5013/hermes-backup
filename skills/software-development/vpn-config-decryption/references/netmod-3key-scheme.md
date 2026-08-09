# NetMod 4.2.0 nm-vmess — the real 3-key AES-128-ECB scheme (cracked 2026-08-08)

Ground-truth source: the shipping APK itself — NetMod VPN Client 4.2.0 (vc=635),
`/tmp/netmod_4.2.0.xapk`, split APK `config.armeabi_v7a.apk` contains
`lib/armeabi-v7a/libgojni.so` (31.5MB, Go 1.24.5, gomobile). Everything below was
read out of that binary with pure-Python tooling (no jadx, no objdump).

## Call chain (dex → native)

1. `Lcom/netmod/syna/model/V2RayModel;.<init>(String)` — the `nm-vmess://` parser.
   Smali flow: `startsWith("nm-vmess://")` → `replace("nm-vmess://", "")` →
   `invoke-static Lnetmodcore/Netmodcore;->b(Ljava/lang/String;)Ljava/lang/String;`
   → `URLDecoder.decode(..., UTF-8)` → `new JSONObject(...)`.
   → So the decrypted result is a **vmess-schema JSON string**, URL-decoded by the app.
2. `Lnetmodcore/Netmodcore;->b` is a **native** method (dex access_flags) → gomobile JNI.
3. Go side: `main._B` → `github.com/eichgee/netmodcore/android.B` →
   `security.Decrypt(s string) string`.

## The decryption (Go `security` package, verified by disassembly)

- `security.Decrypt` (vaddr 0x011582f4): **base64-decodes the input first** (Go
  `base64` Encoding struct at 0x142b9e8, decode core 0x49ed90), copies a **24-byte
  key table from global 0x1E18A08** (copy site 0x3cf554; table = 3× (ptr,len) string
  pairs, built by `security.init.0`), then loops `i` from 0 while `i < 3`, calling
  `security.decryptInner(key, data)` per iteration until one succeeds → **try-loop,
  NOT a chunk split**.
- `security.decryptInner` (0x01158800): dispatches the AES cipher through an
  **interface method pointer** (`ldr r0,[r0,#0xc]`; per-block `ldr r6,[r6,#0x10]`
  → `blx r6`), then `security.pkcs7Unpad` (0x01158b6c), then string-make.
  AES-128-ECB + PKCS#7 over the WHOLE blob (17 blocks for the 272-byte sample) —
  consistent with the devkaj PHP using `AES-128-ECB` raw.
- `security.init.0` (0x01157fd8) builds a **3-element table of base64 key literals**
  (resolved from the Go pc-rel literal pool at file 0x1dfddf0):

| base64 literal in .so (rodata)          | decoded 16-byte key     |
|-----------------------------------------|-------------------------|
| `PG4zdDV5bjRebjN0bTBkPg==`              | `<n3t5yn4^n3tm0d>`      |
| `X25ldHN5bmFfbmV0bW9kXw==`              | `_netsyna_netmod_`      |
| `bmljZXRyeWJ1ZGR5Z29vbg==`              | `nicetrybuddygoon`      |

⚠️ Key0 is `<n3t5yn4^n3tm0d>` — the base64 has a literal **4** (`...bjRe...`), NOT
`<n3t5yn^Nn3tm0d>`. The old devkaj key `_netsyna_netmod_` is still one of the three —
it alone failed because it's simply NOT the key the current app uses (key0 is).

## Why the earlier devkaj single-key test failed

User's real sample: 272 bytes = 17×16-byte blocks, first byte 0xAB, high entropy.
`AES-128-ECB(_netsyna_netmod_)` over the whole blob → garbage. Correct model:
the app tries **key0 first** (`<n3t5yn4^n3tm0d>`), and key0 decrypts the whole
272-byte blob in one ECB run → valid pkcs7 → vmess JSON. Keys 1–2 are legacy
fallbacks (older NetMod configs still decryptable with them).

## Status — FULLY VERIFIED (2026-08-09)

- VERIFIED: keys (base64 literals read from the binary), the 3-key try-loop, the
  dex→native call chain, AES-128-ECB + pkcs7 mode, base64-first wrapper.
- VERIFIED END-TO-END: user's real 272-byte payload decrypts with key0
  `<n3t5yn4^n3tm0d>` (AES-128-ECB, whole blob) → clean vmess JSON:
  `{"add":"www.nagwa.com","port":"443","id":"03fcc618-...","aid":"0","scy":"auto","net":"ws","type":"none","host":"www.nagwa.com.comvaso.dpdns.org","path":"/linkvws","tls":"tls","sni":"www.nagwa.com.comvaso.dpdns.org","ps":"@VOLTAGOO","v":"2"}`
- The payload was stored in state.db id=1392 as a **multi-line message**: line 0 =
  the real `nm-vmess://` code, line 1 = an old bot error string — always split lines
  and take the FIRST `nm-vmess://` occurrence.

## Reusable technique: Go .so symbol extraction (no Go toolchain needed)

A Go Android .so keeps its full symbol table in the pclntab. Steps that worked:

1. Find pcHeader: scan for magic `f1 ff ff ff` (Go ≥1.18). Header layout (32-bit):
   +0 magic(4), +4 pad1, +5 pad2, +6 minLC, +7 ptrSize, +8 nfunc(u4), +12 nfiles(u4),
   +16 textStart(u4), +20 funcnameOffset(u4), +24 cuOffset, +28 filetabOffset,
   +32 pctabOffset, +36 pclnOffset.
2. functab starts at pcHeader+40; entries are (entryoff u4, funcoff u4).
   funcnametab = pcHeader + funcnameOffset; pclntab = pcHeader + pclnOffset.
   `_func` struct at pclntab+funcoff: entryOff u4, nameOff i4 (nameOff is relative to
   funcnametab start); entryOff is relative to textStart.
   Function vaddr = textStart + entryOff.
3. Robust way (androguard-style walking misaligned): scan 4-byte-aligned offsets in
   the pclntab region, treat as `_func`, check nameOff → valid ASCII name → filter.
4. Map vaddr→file offset via ELF LOAD segments (phdr: p_type==1 → offset/vaddr/filesz).
5. Disassemble with `pip install capstone`, `Cs(CS_ARCH_ARM, CS_MODE_ARM)` for
   armeabi-v7a. Go ARM32 code is stack-based (Go register ABI is amd64/arm64 only).
6. Resolve string/table references: Go ARM uses
   `ldr rX,[pc,#imm]` then `add rX, pc, rX` — the literal value is an offset from the
   **add** instruction's PC (add_addr + 8 + literal). The pool value is a relocation
   delta; resolve → absolute vaddr → deref (ptr,len) pairs to get Go strings.
   (Non-relocated packed .so may store pre-linked vaddrs; if a pool value lands past
   EOF, treat the target as .data/.bss and re-derive with segment base math.)

## Pitfalls

- Dex "crypto-looking" strings may belong to bundled SDKs (Google Ads `zzhis`,
  Vungle) — verify the owning class package before hunting.
- androguard `Analysis` API OOMs on big APKs; its instruction API can silently miss
  const-string refs that `grep` proves exist → raw struct-based dex parsing is the
  reliable route (see references/nm-vmess-format.md for the raw parser approach).
- libgojni.so also contains xray-core networking code (huge); the netmodcore Go
  packages (`github.com/eichgee/netmodcore/...`) are the app's own code — filter
  function scans by that prefix.
- `security.gap` XOR-obfuscates strings with 0x18 (`/proc/self/maps`, `.apk` —
  anti-tamper path strings, NOT keys). Don't confuse gap-strings with key material.
- User preference: NO redaction in bot decrypt output; bot dies on container restart.
