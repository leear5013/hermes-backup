# HTTP Injector session 19F probe — jadx deployed; Lite encryption material surfaced (2026-08-10)

Continuation of session 19E (deobfuscator chain cracked in Java). Goal: find the cloud-blob PBE password / AES key for the `POST https://www.ehiapp.com/httpinjector/config` blob.

## Tooling: jadx 1.5.0 now on the VPS (first decompiler that works here)
- `apt-get install -y default-jdk` (Java 21.0.11, includes javac; `default-jre-headless` alone has no javac).
- `curl -sL -o jadx.zip https://github.com/skylot/jadx/releases/download/v1.5.0/jadx-1.5.0.zip` (104,967,983 B).
- `apt-get install -y unzip && unzip -q -o jadx.zip -d jadx` → `jadx/bin/jadx`.
- Decompile: `./jadx/bin/jadx -d jadx_out <apk> --no-res -q` (fast; Lite 8.2MB ≈ 1 min).
- **Coverage verification is MANDATORY**: grep the `jadx_out/sources` tree for strings you KNOW are in the APK (e.g. `ehi.tools`, `ehiapp.com`, `EncryptedApi`). Obfuscated `com.google.android.gms.internal.*` classes with Unicode names either come out renamed (`C1407.java` = `ۂ` ContextWrapper, `yl.java` = gson UnsafeAllocator) or VANISH entirely. For ehi_lite531.apk: grep `ehi.tools|ehiapp` → **0 hits**; `BaseApplication` (the Unseal/artMethod reflection class) did not decompile at all. → jadx is NOT a substitute for androguard bytecode dumps on the obfuscated classes; use it for readable packages (model/utils/event) + resources only.

## New encryption material (Lite 5.3.1, `utils/Constant.java` — full content)
```java
public class Constant {
    public static final String API_VERSIONINFO = "/apps/injector/update/?type=android";
    private static final String DES_MODE = "DES/ECB/PKCS5Padding";
    public static final boolean ENCRYPTION = true;
    private static final String HASH_ALGORITHM = "SHA-256";
    public static final String INJECTOR_CONNECTED = "com.evozi.injector.lite.CONNECTED";
    public static final String INJECTOR_DISCONNECTED = "com.evozi.injector.lite.DISCONNECTED";
    public static final String SIGNATURE = "ARsgBGVYjoAFCF0NR0v89Og0ezAkFw1rpOg0ZfA==";  // 44 chars b64 = 32 bytes
    public static final String UNIVERSAL_KEY = "BtUFur2znnfSFKakGRaL1QFcsq9G5bTIVlV5HIzXWCcJIoFAcB8BySN0bmTPrqGD7j75azc9wIIstJZbqjvWu051XTgnZul3Nj5oNct1uWZ68JtF0wQj462Wu9AoWj2Lf4MQvVzxj1Q5";  // ~256 chars b64 = 192 bytes
    public static final String WEB_CHECK_IP = "/ip_ui";
    public static char[] XOR_KEY = {'E', 'V', 'O', 'Z', 'I'};
}
```
- **UNIVERSAL_KEY** — never seen in any main-app .so pool; 192 decoded bytes is too long for AES → try as (a) Tozny PBE password (UTF-8 chars), (b) first 32 bytes as AES-256-CBC key, (c) raw b64 string as PBE password.
- **XOR_KEY "EVOZI"** — matches Evozi signing style; try as PBE password / XOR first layer.
- **SIGNATURE** (32 bytes decoded) — try as raw AES-256-CBC key.

## Profile.java = the cloud blob PLAINTEXT SHAPE (validation oracle)
The decrypted cloud config is a **Profile JSON**. Fields: `configExpiryTimestamp`(long), `configHwid`, `configIdentifier`, `configMessage`, `configSalt`, `configTimestamp`(long), `configVersionCode`(int), `customDns1/2`, `customRoutes`, `dnsType`, `excludedRoutes`, `host`, `isCompression`, `isConfigLock`, `isDNSProxy`, `isDefaultRoute`, `isPublicKey`, `isUpstreamProxy`, `localPort`, `lockModes`, `lockModesHash`, `overwriteServerData`, `overwriteServerProxyPort`, `overwriteServerType`, `password`, `payload`, `port`, `publicKey`, `remoteProxy`, `remoteProxyAuth`, `remoteProxyPassword/Username`, `shadowsocksEncryptionMethod/Host/Password/Port`, `sniHostname`, `startSsh`, `tunnelType`, `upstreamProxy`, `user`.
→ Candidate-key validation: plaintext must `json.loads()` AND contain ≥2 of `{configSalt, configIdentifier, configTimestamp, configHwid, payload, host}`. (Much stronger than the old printable-ratio test.)

## Dead-end confirmation (Retrofit annotations)
- androguard 4.1.4 — five variants tried, ALL dead: `EncodedMethod` has no `get_annotations`/`get_class_def`; `DEX` has no `get_classdefs`; `get_classes_def_item()` returns non-iterable `ClassHDefItem` (attrs: CM, class_def, get_class_idx, get_length, get_method, get_names, get_obj, get_off, get_raw, offset, set_off, show).
- jadx also produced NO source for the Retrofit interface `ᵤ` (the 4 `Call`-returning methods: `ﾠ⁪͏(String,String,int)`, `ﾠ⁫⁫(String,String,String)`, `ﾠ⁬͏(String,String,int)`, `ﾠ⁮͏(String,String,String,String)`). The `/httpinjector/*` path + request-shape annotations remain statically unreachable — trace callers instead.

## New API path (untested)
- `/apps/injector/update/?type=android` (Lite `API_VERSIONINFO`) — probe on `www.ehiapp.com` + `www.ehi.tools`.

## Class-confirmation (from bytecode + jadx)
- `gb.ﾠ⁬͏(SharedPreferences)` = shadowsocks `ss://` URI builder (uses `BaseApplication.lI` native + `x6.ﾠ⁮͏` hash) — dead lead, NOT cloud.
- `e2.<init>`/`ﾠ⁮͏(String)` = Retrofit `baseUrl` setter (host from SharedPreferences — consistent with runtime-constructed base host).
- `EncryptedApi` = `{data:String, status:int}` only — Gson model for the API response wrapper.

## Next steps
1. Test UNIVERSAL_KEY variants + "EVOZI" + SIGNATURE bytes as Tozny PBE password (PBKDF2WithHmacSHA1 → 384-bit → 16B AES + 32B HMAC) AND as raw AES-CBC (blob[:16] IV / blob[16:] ct, plus whole-blob layout) against the main-app blob.
2. Trace `helper/ﾠ⁬͏.ﾠ⁭(Context,int)` — the untraced PBE caller (password source = the live lead).
3. Probe `/apps/injector/update/?type=android` on both API hosts.
