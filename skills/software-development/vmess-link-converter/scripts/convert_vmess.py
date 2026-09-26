#!/usr/bin/env python3
"""
Standalone VMess Link Converter and Decryptor.
Supports:
  - nm-vmess:// (NetMod AES-128-ECB)
  - vmess:// (Base64 JSON / Plain URI / Shadowrocket)
  - Raw JSON
Uses Python's standard cryptography library (no external pycryptodome required).
"""

import sys
import json
import base64
import argparse
import urllib.parse
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

NETMOD_KEYS = [
    b"<n3t5yn4^n3tm0d>",
    b"_netsyna_netmod_",
    b"nicetrybuddygoon"
]

def aes_ecb_decrypt(ciphertext: bytes, key: bytes) -> bytes:
    cipher = Cipher(algorithms.AES(key[:16]), modes.ECB(), backend=default_backend())
    decryptor = cipher.decryptor()
    return decryptor.update(ciphertext) + decryptor.finalize()

def aes_ecb_encrypt(plaintext: bytes, key: bytes) -> bytes:
    pad_len = 16 - (len(plaintext) % 16)
    padded = plaintext + bytes([pad_len]) * pad_len
    cipher = Cipher(algorithms.AES(key[:16]), modes.ECB(), backend=default_backend())
    encryptor = cipher.encryptor()
    return encryptor.update(padded) + encryptor.finalize()

def decrypt_nm_vmess(payload_b64: str, explicit_key: bytes = None) -> dict:
    raw = base64.b64decode(payload_b64)
    keys_to_try = [explicit_key] if explicit_key else NETMOD_KEYS
    for key in keys_to_try:
        if not key:
            continue
        try:
            dec = aes_ecb_decrypt(raw, key)
            pad_len = dec[-1]
            if 1 <= pad_len <= 16 and dec[-pad_len:] == bytes([pad_len]) * pad_len:
                dec = dec[:-pad_len]
            txt = dec.decode('utf-8')
            return json.loads(txt)
        except Exception:
            continue
    raise ValueError("Failed to decrypt nm-vmess payload with known NetMod keys.")

def encrypt_nm_vmess(config: dict, key: bytes = NETMOD_KEYS[0]) -> str:
    raw_json = json.dumps(config, separators=(',', ':')).encode('utf-8')
    enc = aes_ecb_encrypt(raw_json, key)
    return "nm-vmess://" + base64.b64encode(enc).decode('utf-8')

def parse_vmess(input_str: str, key: bytes = None) -> dict:
    s = input_str.strip()
    if s.startswith("nm-vmess://"):
        return decrypt_nm_vmess(s[len("nm-vmess://"):], explicit_key=key)
    elif s.startswith("vmess://"):
        raw = s[len("vmess://"):]
        if "@" in raw or "?" in raw:
            parsed = urllib.parse.urlparse(s)
            user_info = parsed.username or ""
            host = parsed.hostname or ""
            port = str(parsed.port or 443)
            query = urllib.parse.parse_qs(parsed.query)
            remark = urllib.parse.unquote(parsed.fragment or "")
            return {
                "v": "2",
                "ps": remark,
                "add": host,
                "port": port,
                "id": user_info,
                "aid": "0",
                "scy": query.get("security", ["auto"])[0],
                "net": query.get("type", ["tcp"])[0],
                "type": "none",
                "host": query.get("host", [""])[0],
                "path": query.get("path", [""])[0],
                "tls": query.get("security", [""])[0] if query.get("security", [""])[0] in ["tls", "reality"] else "",
                "sni": query.get("sni", [""])[0],
                "fp": query.get("fp", [""])[0]
            }
        else:
            rem = len(raw) % 4
            if rem > 0:
                raw += "=" * (4 - rem)
            dec = base64.b64decode(raw).decode('utf-8')
            return json.loads(dec)
    elif s.startswith("{") and s.endswith("}"):
        return json.loads(s)
    else:
        raise ValueError("Unrecognized VMess format.")

def to_base64_vmess(config: dict) -> str:
    s = json.dumps(config, separators=(',', ':'))
    return "vmess://" + base64.b64encode(s.encode('utf-8')).decode('utf-8')

def to_plain_uri(config: dict) -> str:
    params = {}
    if config.get("net"): params["type"] = config["net"]
    if config.get("tls"): params["security"] = config["tls"]
    if config.get("path"): params["path"] = config["path"]
    if config.get("host"): params["host"] = config["host"]
    if config.get("sni"): params["sni"] = config["sni"]
    if config.get("fp"): params["fp"] = config["fp"]
    query = urllib.parse.urlencode(params)
    remark = urllib.parse.quote(config.get("ps", ""))
    return f"vmess://{config.get('id', '')}@{config.get('add', '')}:{config.get('port', 443)}?{query}#{remark}"

def to_shadowrocket(config: dict) -> str:
    userinfo = base64.b64encode(f"{config.get('scy', 'auto')}:{config.get('id', '')}@{config.get('add', '')}:{config.get('port', 443)}".encode()).decode()
    params = {
        "remarks": config.get("ps", ""),
        "obfsParam": config.get("host", ""),
        "path": config.get("path", ""),
        "obfs": "websocket" if config.get("net") == "ws" else config.get("net", "none"),
        "tls": "1" if config.get("tls") in ["tls", "reality"] else "0",
        "peer": config.get("sni", ""),
        "allowInsecure": "0"
    }
    return f"vmess://{userinfo}?{urllib.parse.urlencode(params)}"

def main():
    parser = argparse.ArgumentParser(description="Convert/Decrypt VMess links.")
    parser.add_argument("input", help="VMess link (nm-vmess://, vmess://, or JSON string)")
    parser.add_argument("--format", choices=["all", "base64", "uri", "shadowrocket", "json", "nm-vmess"], default="all", help="Output format")
    parser.add_argument("--key", help="AES key for nm-vmess decryption/encryption (optional)")
    parser.add_argument("-o", "--output", help="Write result to file instead of stdout")
    args = parser.parse_args()

    key_bytes = args.key.encode('utf-8') if args.key else None
    try:
        config = parse_vmess(args.input, key=key_bytes)
    except Exception as e:
        sys.stderr.write(f"Error parsing input: {e}\n")
        sys.exit(1)

    output_lines = []
    if args.format == "all":
        output_lines.append("=== Decrypted JSON Config ===")
        output_lines.append(json.dumps(config, indent=2))
        output_lines.append("\n=== Standard Base64 VMess Link (v2rayNG / V2RayN) ===")
        output_lines.append(to_base64_vmess(config))
        output_lines.append("\n=== Plain URI Format (URL Scheme) ===")
        output_lines.append(to_plain_uri(config))
        output_lines.append("\n=== Shadowrocket Format ===")
        output_lines.append(to_shadowrocket(config))
        output_lines.append("\n=== Re-encrypted NetMod Link (nm-vmess://) ===")
        output_lines.append(encrypt_nm_vmess(config, key=key_bytes or NETMOD_KEYS[0]))
    elif args.format == "base64":
        output_lines.append(to_base64_vmess(config))
    elif args.format == "uri":
        output_lines.append(to_plain_uri(config))
    elif args.format == "shadowrocket":
        output_lines.append(to_shadowrocket(config))
    elif args.format == "json":
        output_lines.append(json.dumps(config, indent=2))
    elif args.format == "nm-vmess":
        output_lines.append(encrypt_nm_vmess(config, key=key_bytes or NETMOD_KEYS[0]))

    res = "\n".join(output_lines)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(res + "\n")
    else:
        print(res)

if __name__ == "__main__":
    main()
