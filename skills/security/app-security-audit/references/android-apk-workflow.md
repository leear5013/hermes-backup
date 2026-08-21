# Android APK audit workflow (validated on Babbel 21.53.0, 2026-08-21)

## 1. Acquire the APK — APKMirror chain (all hops required)

```bash
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) ... Chrome/120 Safari/537.36"
# hop 1: search
curl -sL -A "$UA" "https://www.apkmirror.com/?post_type=app_release&searchtype=apk&s=<app>"
# hop 2: release page → hop 3: variant/download page (follow the /download link)
# hop 4: inside that page find id="download-link" href="/wp-content/themes/APKMirror/download.php?id=..&key=..&forcebaseapk=true"
curl -sL -A "$UA" -e "<the download page URL>" "https://www.apkmirror.com<that href>" -o app.apk
head -c 8 app.apk | od -c   # must be PK\x03\x04, else you got an HTML interstitial
```
APKPure blocks datacenter IPs (403). APKMirror works but needs Referer per hop.

## 2. Tooling reality check (this box = ~1GB cgroup)

```bash
cat /sys/fs/cgroup/memory.max          # check BEFORE choosing tools
apt-get install -y default-jre-headless unzip   # java 21 OK
pip install --target=/opt/work/pylibs androguard==3.3.5
```
- jadx: `tools/bin/jadx -d jadx-out --no-res -j N app.apk` → dies exit 137 even at
  `-Xmx700m`/`-j1` on a 100MB APK. **One attempt max**, then low-memory path.
- Low-memory path (works fully): androguard `APK()` for manifest + components +
  intent filters; raw dex byte-regex for strings/secrets over unzipped classes*.dex.

## 3. Manifest extraction (binary AXML — never plaintext)

```python
data = open('AndroidManifest.xml','rb').read()
txt = data.decode('utf-16-le', errors='ignore') + data.decode('utf-8', errors='ignore')
strs = list(dict.fromkeys(re.findall(r'[\x20-\x7e]{3,}', txt)))
```
Pull out: permissions, schemes/hosts (deep links), exported components,
allowBackup/usesCleartextTraffic/networkSecurityConfig flags.
androguard gives structured versions:
`apk.get_android_manifest_xml()`, iterate `{http://schemas.android.com/apk/res/android}name/exported`.

## 4. Secret hunt regex bank (raw dex bytes)

```python
PATS = {
 'google_api_key': rb'AIza[0-9A-Za-z\-_]{20,}',
 'aws_key':        rb'AKIA[0-9A-Z]{16}',
 'jwt':            rb'eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{5,}',
 'basic_auth':     rb'Basic\s+[A-Za-z0-9+/=]{16,}',
 'slack':          rb'xox[baprs]-[0-9A-Za-z\-]{10,}',
 'stripe':         rb'(sk|pk)_(live|test)_[0-9a-zA-Z]{20,}',
 'hex32':          rb'\b[a-f0-9]{32}\b',
}
```
For each hit, print surrounding printable strings to identify the owning SDK
(e.g. hex32 hits next to `adjustTracker` = Adjust SDK client tokens = by design).
Also enumerate ALL https URLs in the dex pool — staging hosts hide there
(`api.*staging*`, `-dev`, internal TLDs). Probe each once, unauthenticated GET.

## 5. Checklist that produced 6 findings on Babbel

- network_security_config.xml (res/xml/, binary AXML): cleartext rules, trust anchors
- backup_descriptor.xml / dataExtractionRules: what's in the cloud-backup set
- Realm DB encryption markers (`encryptionKey`, SQLCipher) vs allowBackup=true
- Certificate pinning: OkHttp CertificatePinner class present ≠ pins configured;
  grep for literal `sha256/<43 chars>` — zero hits means no pinning
- Exported activities with custom schemes (deep-link injection surface)
- Dev-config/debug UI packages shipped in release (grep package name refs)
- EncryptedSharedPreferences present? auth tokens stored where?
- Service-discovery/config endpoints: often unauthenticated AND token-bearing

## Report skeleton (what triagers accept)

Executive table (# | finding | severity | status) → per finding: Description,
PoC (real commands + real output), Impact, Remediation w/ MASVS ref →
"Checked and found sound" section (proves boundary testing) → Reproduction
notes (build source, hashes, dates, no-data-retained statement).
Save under `/opt/work/<t>-audit/Report.md`; copy final to /data/workspace/.
