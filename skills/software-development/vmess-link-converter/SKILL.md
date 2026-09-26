---
name: vmess-link-converter
description: "Convert and decrypt VMess links: nm-vmess, base64, URI."
version: 1.0.0
author: Hesham Hatem (leear5013), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [vmess, nm-vmess, vpn, netmod, shadowrocket, v2ray, xray]
    related_skills: [vpn-config-conversion, vmess-decrypt-bot-hosting]
---

# VMess Link Converter

Convert, decrypt, and normalize VMess configurations across different formats: NetMod (`nm-vmess://`), standard V2Ray/v2rayNG (`vmess://<base64-json>`), human-readable plain URI (`vmess://<uuid>@<host>:<port>?...#<remark>`), and Shadowrocket format.

## When to Use
- User provides a NetMod link (`nm-vmess://...`) and wants it decrypted or converted to standard VMess.
- Converting between Base64 JSON and plain human-readable URI or Shadowrocket scheme.
- Inspecting or modifying fields of an encrypted or encoded VMess profile.
- Re-encrypting a plain config into `nm-vmess://` format.

## Formats Handled
1. **NetMod (`nm-vmess://`)**: AES-128-ECB encrypted with NetMod standard keys (`<n3t5yn4^n3tm0d>`, `_netsyna_netmod_`, `nicetrybuddygoon`).
2. **Standard Base64 JSON (`vmess://`)**: Used by V2RayN, v2rayNG, NekoBox, Matsuri.
3. **Plain URI (`vmess://<uuid>@<host>:<port>?...#<tag>`)**: Standard URL scheme for Xray/V2Ray.
4. **Shadowrocket (`vmess://<base64-credentials>?...`)**: Scheme used by iOS Shadowrocket.
5. **Raw JSON**: Plain dictionary representation of the VMess profile.

## How to Run

Invoke the standalone script via `terminal`:

```bash
python3 /data/.hermes/skills/networking/vmess-link-converter/scripts/convert_vmess.py "<input_link_or_json>" [options]
```

### Options:
- `--format {all,base64,uri,shadowrocket,json,nm-vmess}`: Output format (default: `all`).
- `-o, --output <file>`: Write output to a file instead of stdout.
- `--key <key>`: Specific AES key to use for `nm-vmess` (default: auto try-loop).

## Quick Reference

Convert an `nm-vmess://` link to standard base64 `vmess://`:
```bash
python3 /data/.hermes/skills/networking/vmess-link-converter/scripts/convert_vmess.py "nm-vmess://..." --format base64
```

Convert to human-readable plain URI:
```bash
python3 /data/.hermes/skills/networking/vmess-link-converter/scripts/convert_vmess.py "nm-vmess://..." --format uri
```

Show all formats (including pretty JSON breakdown):
```bash
python3 /data/.hermes/skills/networking/vmess-link-converter/scripts/convert_vmess.py "nm-vmess://..." --format all
```

Re-encrypt a JSON config into `nm-vmess://`:
```bash
python3 /data/.hermes/skills/networking/vmess-link-converter/scripts/convert_vmess.py '{"add":"example.com",...}' --format nm-vmess
```

## Pitfalls
- `nm-vmess://` uses AES-128-ECB with PKCS7 padding. The primary key `<n3t5yn4^n3tm0d>` includes the literal angle brackets `<>` (16 bytes total).
- Using system `cryptography` library avoids third-party dependency issues like missing `pycryptodome`.
- When converting to plain URI, query parameters must be properly URL-encoded (especially `path` with slashes and `remarks` with emojis or spaces).
