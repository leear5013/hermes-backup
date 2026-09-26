#!/usr/bin/env python3
"""
Standalone VMess & VLESS Link Converter and Decryptor.
Supports:
  - nm-vmess://, nm-vless:// (NetMod AES-128-ECB)
  - vmess:// (Base64 JSON / Plain URI / Shadowrocket)
  - vless:// (Standard Xray/V2Ray URI)
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

def decrypt_nm_payload(payload_b64: str, explicit_key: bytes = None):
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
            txt_clean = txt.strip()
            if txt_clean.startswith("{") and txt_clean.endswith("}"):
                return json.loads(txt_clean), "json", key
            else:
                return txt_clean, "uri", key
        except Exception:
            continue
    raise ValueError("Failed to decrypt NetMod payload with known NetMod keys.")

def is_insecure_needed(config: dict) -> bool:
    if config.get("insecure") in [True, "1", 1] or config.get("allowInsecure") in [True, "1", 1]:
        return True
    add = config.get("add", "")
    sni = config.get("sni", "")
    host = config.get("host", "")
    if sni and sni != add:
        return True
    if host and host != add:
        return True
    return False

def parse_link(input_str: str, key: bytes = None):
    s = input_str.strip()
    if s.startswith("nm-vless://"):
        content, kind, used_key = decrypt_nm_payload(s[len("nm-vless://"):], explicit_key=key)
        if kind == "uri":
            vless_uri = content if content.startswith("vless://") else "vless://" + content
            return {"proto": "vless", "uri": vless_uri, "key": used_key}
        else:
            return {"proto": "vless", "config": content, "key": used_key}

    elif s.startswith("vless://"):
        return {"proto": "vless", "uri": s, "key": None}

    elif s.startswith("nm-vmess://"):
        content, kind, used_key = decrypt_nm_payload(s[len("nm-vmess://"):], explicit_key=key)
        if kind == "json":
            return {"proto": "vmess", "config": content, "key": used_key}
        else:
            # URI format inside nm-vmess
            return {"proto": "vmess", "config": parse_vmess_uri(content), "key": used_key}

    elif s.startswith("vmess://"):
        raw = s[len("vmess://"):]
        if "@" in raw or "?" in raw:
            return {"proto": "vmess", "config": parse_vmess_uri(s), "key": None}
        else:
            rem = len(raw) % 4
            if rem > 0:
                raw += "=" * (4 - rem)
            dec = base64.b64decode(raw).decode('utf-8')
            return {"proto": "vmess", "config": json.loads(dec), "key": None}

    elif s.startswith("{") and s.endswith("}"):
        return {"proto": "vmess", "config": json.loads(s), "key": None}
    else:
        raise ValueError("Unrecognized link format (supported: nm-vmess://, nm-vless://, vmess://, vless://, json).")

def parse_vmess_uri(s: str) -> dict:
    parsed = urllib.parse.urlparse(s if s.startswith("vmess://") else "vmess://" + s)
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

def normalize_vless_uri(raw_uri: str, insecure: bool = None) -> tuple[str, dict]:
    parsed = urllib.parse.urlsplit(raw_uri)
    qs = urllib.parse.parse_qs(parsed.query)
    params = {k: v[0] for k, v in qs.items()}
    
    # Check SNI spoofing
    host_addr = parsed.hostname or ""
    sni = params.get("sni", "")
    host_header = params.get("host", "")
    spoof = (sni and sni != host_addr) or (host_header and host_header != host_addr)
    
    use_insecure = insecure if insecure is not None else spoof
    if use_insecure:
        params["insecure"] = "1"
        
    # Rebuild clean query
    query_items = [f"{k}={urllib.parse.quote(v, safe='')}" for k, v in params.items()]
    new_query = "&".join(query_items)
    remark_encoded = urllib.parse.quote(urllib.parse.unquote(parsed.fragment))
    norm_link = f"vless://{parsed.netloc}?{new_query}#{remark_encoded}"
    
    info = {
        "uuid": parsed.username or "",
        "add": host_addr,
        "port": str(parsed.port or 443),
        "remark": urllib.parse.unquote(parsed.fragment),
        "params": params
    }
    return norm_link, info

def to_base64_vmess(config: dict) -> str:
    s = json.dumps(config, separators=(',', ':'))
    return "vmess://" + base64.b64encode(s.encode('utf-8')).decode('utf-8')

def to_plain_uri(config: dict, insecure: bool = None) -> str:
    params = {}
    if config.get("net"): params["type"] = config["net"]
    if config.get("tls"): params["security"] = config["tls"]
    if config.get("path"): params["path"] = config["path"]
    if config.get("host"): params["host"] = config["host"]
    if config.get("sni"): params["sni"] = config["sni"]
    if config.get("fp"): params["fp"] = config["fp"]
    
    use_insecure = insecure if insecure is not None else is_insecure_needed(config)
    if use_insecure and config.get("tls") in ["tls", "reality"]:
        params["insecure"] = "1"
        
    query = urllib.parse.urlencode(params)
    remark = urllib.parse.quote(config.get("ps", ""))
    return f"vmess://{config.get('id', '')}@{config.get('add', '')}:{config.get('port', 443)}?{query}#{remark}"

def to_shadowrocket(config: dict, insecure: bool = None) -> str:
    userinfo = base64.b64encode(f"{config.get('scy', 'auto')}:{config.get('id', '')}@{config.get('add', '')}:{config.get('port', 443)}".encode()).decode()
    use_insecure = insecure if insecure is not None else is_insecure_needed(config)
    params = {
        "remarks": config.get("ps", ""),
        "obfsParam": config.get("host", ""),
        "path": config.get("path", ""),
        "obfs": "websocket" if config.get("net") == "ws" else config.get("net", "none"),
        "tls": "1" if config.get("tls") in ["tls", "reality"] else "0",
        "peer": config.get("sni", ""),
        "allowInsecure": "1" if use_insecure else "0"
    }
    return f"vmess://{userinfo}?{urllib.parse.urlencode(params)}"

def encrypt_nm(content: str, key: bytes = NETMOD_KEYS[0], prefix: str = "nm-vmess://") -> str:
    enc = aes_ecb_encrypt(content.encode('utf-8'), key)
    return prefix + base64.b64encode(enc).decode('utf-8')

def main():
    parser = argparse.ArgumentParser(description="Convert/Decrypt VMess and VLESS links.")
    parser.add_argument("input", help="Link (nm-vmess://, nm-vless://, vmess://, vless://, or JSON)")
    parser.add_argument("--format", choices=["all", "base64", "uri", "shadowrocket", "json", "nm-vmess", "nm-vless", "vless"], default="all", help="Output format")
    parser.add_argument("--key", help="AES key for NetMod decryption/encryption (optional)")
    parser.add_argument("--insecure", action="store_true", default=None, help="Force allowInsecure=1 / insecure=1")
    parser.add_argument("-o", "--output", help="Write result to file instead of stdout")
    args = parser.parse_args()

    key_bytes = args.key.encode('utf-8') if args.key else None
    try:
        parsed_data = parse_link(args.input, key=key_bytes)
    except Exception as e:
        sys.stderr.write(f"Error parsing input: {e}\n")
        sys.exit(1)

    proto = parsed_data["proto"]
    output_lines = []

    if proto == "vless":
        raw_uri = parsed_data.get("uri")
        norm_vless, info = normalize_vless_uri(raw_uri, insecure=args.insecure)
        if args.format in ["all", "vless", "uri"]:
            if args.format == "all":
                output_lines.append("=== Decrypted VLESS Details ===")
                output_lines.append(f"Address:  {info['add']}")
                output_lines.append(f"Port:     {info['port']}")
                output_lines.append(f"UUID:     {info['uuid']}")
                output_lines.append(f"Remark:   {info['remark']}")
                output_lines.append(f"Params:   {json.dumps(info['params'], indent=2)}")
                output_lines.append("\n=== Standard VLESS Link (v2rayNG / NekoBox / Xray) ===")
                output_lines.append(norm_vless)
                output_lines.append("\n=== Re-encrypted NetMod Link (nm-vless://) ===")
                output_lines.append(encrypt_nm(norm_vless[len("vless://"):], key=parsed_data.get("key") or NETMOD_KEYS[0], prefix="nm-vless://"))
            else:
                output_lines.append(norm_vless)
        elif args.format == "json":
            output_lines.append(json.dumps(info, indent=2))
        elif args.format == "nm-vless":
            output_lines.append(encrypt_nm(norm_vless[len("vless://"):], key=parsed_data.get("key") or NETMOD_KEYS[0], prefix="nm-vless://"))

    elif proto == "vmess":
        config = parsed_data["config"]
        if args.format == "all":
            output_lines.append("=== Decrypted JSON Config ===")
            output_lines.append(json.dumps(config, indent=2))
            output_lines.append("\n=== Standard Base64 VMess Link (v2rayNG / V2RayN) ===")
            output_lines.append(to_base64_vmess(config))
            output_lines.append("\n=== Plain URI Format (URL Scheme) ===")
            output_lines.append(to_plain_uri(config, insecure=args.insecure))
            output_lines.append("\n=== Shadowrocket Format ===")
            output_lines.append(to_shadowrocket(config, insecure=args.insecure))
            output_lines.append("\n=== Re-encrypted NetMod Link (nm-vmess://) ===")
            raw_json = json.dumps(config, separators=(',', ':'))
            output_lines.append(encrypt_nm(raw_json, key=parsed_data.get("key") or NETMOD_KEYS[0], prefix="nm-vmess://"))
        elif args.format == "base64":
            output_lines.append(to_base64_vmess(config))
        elif args.format == "uri":
            output_lines.append(to_plain_uri(config, insecure=args.insecure))
        elif args.format == "shadowrocket":
            output_lines.append(to_shadowrocket(config, insecure=args.insecure))
        elif args.format == "json":
            output_lines.append(json.dumps(config, indent=2))
        elif args.format == "nm-vmess":
            raw_json = json.dumps(config, separators=(',', ':'))
            output_lines.append(encrypt_nm(raw_json, key=parsed_data.get("key") or NETMOD_KEYS[0], prefix="nm-vmess://"))

    res = "\n".join(output_lines)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(res + "\n")
    else:
        print(res)

if __name__ == "__main__":
    main()
