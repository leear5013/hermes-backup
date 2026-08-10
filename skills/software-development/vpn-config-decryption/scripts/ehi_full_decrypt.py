#!/usr/bin/env python3
"""HTTP Injector .ehi FULL decryptor (verified 2026-08-10 on a real Turkcell TR .ehi).

Pipeline: .ehi container -> L1 AES-256-CBC (3 SideIvs + 3 StandardIvs try-loop)
-> colon-split -> L2 AES-128-CBC -> XXTEA (EOO_MASTER_KEY) -> outer JSON
-> [bypass: config is final] | [standard: xor-layer -> b64 -> Argon2id
-> ChaCha20-Poly1305-X -> inner JSON] -> per-field xor/EHIMSG decode.

Cross-checked against FrontierTM/Pantegnos modules/impl/ehi.go constants and the
zhgddm/npv- HTTPINJECTOR.py reference. Deps: pycryptodome, argon2-cffi
(install into the GATEWAY venv: /opt/venv/bin/pip install pycryptodome argon2-cffi).

Usage: /opt/venv/bin/python ehi_full_decrypt.py <file.ehi> [out.json]
"""
import base64, binascii, hashlib, json, struct, sys
from Crypto.Cipher import AES, ChaCha20_Poly1305
from Crypto.Util.Padding import unpad
import argon2.low_level
from argon2.low_level import Type

# ---------------- constants (from ehi.go / zhgddm HTTPINJECTOR.py) ----------------
L1Key = bytes.fromhex("7e1210f7aab956f7a668bda6e57feddb7f84ad840aef8d27b1b969959be3ab6c")   # 32B AES-256
L2KeyStatic = bytes.fromhex("b2bc617c32d8b9eb1943a5ffa8051eea")                            # 16B AES-128
EooMasterKey = b"null=V5kU5+FFrY\x00"
SideIvs = [
    bytes.fromhex("221d572349555f1d112133236b1f4a3f"),
    bytes.fromhex("5543494c53443e3f4a6a4539384e776a"),
    bytes.fromhex("374c2541575e4d531a3c327b75431e5f"),
]
StandardIvs = [
    bytes.fromhex("2c5d1147bbad422b3b334d4d235f1a53"),
    bytes.fromhex("522b01433a5e8b2fc7549e1ad368e541"),
    bytes.fromhex("337a1035aaedf3458ca167e92d74b839"),
]
allIVs = SideIvs + StandardIvs
CustomAlphabet = "RkLC2QaVMPYgGJW/A4f7qzDb9e+t6Hr0Zp8OlNyjuxKcTw1o5EIimhBn3UvdSFXs"
MASTER_KEY_FIELDS = [
    ("configAesKey", False), ("configIdentifier", False), ("configSalt", False),
    ("configTimestamp", True), ("configExpiryTimestamp", True),
    ("lockModes", False), ("lockModesHash", False), ("configHwid", False),
    ("configLockMobileOperatorId", False),
]

# ---------------- helpers ----------------
def py_str(v):
    if v is None: return ""
    if isinstance(v, bool): return "True" if v else "False"
    if isinstance(v, (int, float)):
        return str(int(v)) if v == int(v) else str(v)
    return str(v)

def py_truthy(v):
    if v is None: return False
    if isinstance(v, str): return v != ""
    if isinstance(v, bool): return v
    if isinstance(v, (int, float)): return v != 0
    return True

def custom_b64_decode(s):
    clean = s.replace("?", "")
    if len(clean) % 4: clean += "=" * (4 - len(clean) % 4)
    std_table = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
    return base64.b64decode(clean.translate(str.maketrans(CustomAlphabet, std_table)))

def decrypt_xor_layer(ct_str, key):
    """reverse -> custom-b64 -> hex -> xor(key) -> drop 0x00. Returns str."""
    if ct_str.strip() == "": return ct_str
    hex_bytes = custom_b64_decode(ct_str[::-1])
    hex_str = hex_bytes.decode('ascii', errors='ignore')
    if len(hex_str) % 2: hex_str = "0" + hex_str
    raw = binascii.unhexlify(hex_str)
    key_b = key.encode() if isinstance(key, str) else key
    out = bytearray()
    for i, b in enumerate(raw):
        x = b ^ key_b[i % len(key_b)]
        if x != 0: out.append(x)
    pt = bytes(out)
    if pt:
        bad = sum(1 for c in pt if c < 32 and c not in (9, 10, 13))
        if bad / len(pt) > 0.5: raise ValueError("entropy check failed")
    return pt.decode('utf-8', errors='replace')

def decode_config_message(ct_str):
    """configMessage: b64 -> UTF-8 -> UTF-16BE units XORed with 'EHIMSG' (Java char semantics)."""
    if ct_str.strip() == "": return ct_str
    padded = ct_str + "=" * ((4 - len(ct_str) % 4) % 4)
    raw = base64.b64decode(padded)
    utf16_bytes = raw.decode('utf-8', errors='replace').encode('utf-16-be', errors='surrogatepass')
    num = len(utf16_bytes) // 2
    java_chars = struct.unpack(f'>{num}H', utf16_bytes)
    key_chars = [ord(c) for c in "EHIMSG"]
    xored = [jc ^ key_chars[i % 6] for i, jc in enumerate(java_chars)]
    xored_bytes = struct.pack(f'>{num}H', *xored)
    return xored_bytes.decode('utf-16-be', errors='surrogatepass').encode('utf-16', 'surrogatepass').decode('utf-16')

def xxtea_decrypt(data, key):
    if not data: return b""
    if len(data) % 4: data += b"\x00" * (4 - len(data) % 4)
    k = struct.unpack("<4I", key.ljust(16, b"\x00")[:16])
    n = len(data) // 4
    v = list(struct.unpack(f"<{n}I", data))
    delta = 0x9e3779b9
    sum_val = ((6 + 52 // n) * delta) & 0xffffffff
    y = v[0]
    while sum_val != 0:
        e = (sum_val >> 2) & 3
        for p in range(n - 1, 0, -1):
            z = v[p - 1]
            mx = (((z >> 5) ^ (y << 2)) + ((y >> 3) ^ (z << 4))) ^ ((sum_val ^ y) + (k[(p & 3) ^ e] ^ z))
            y = v[p] = (v[p] - mx) & 0xffffffff
        z = v[n - 1]
        mx = (((z >> 5) ^ (y << 2)) + ((y >> 3) ^ (z << 4))) ^ ((sum_val ^ y) + (k[0 ^ e] ^ z))
        y = v[0] = (v[0] - mx) & 0xffffffff
        sum_val = (sum_val - delta) & 0xffffffff
    dec = struct.pack(f"<{n}I", *v)
    length = v[-1]
    if 0 < length <= n * 4: return dec[:length]
    return dec.rstrip(b"\x00")

def aes_cbc_decrypt(ct, key, iv):
    c = AES.new(key, AES.MODE_CBC, iv)
    return unpad(c.decrypt(ct), 16)

def parse_ehi_bytes(file_bytes):
    r = bytes(file_bytes); off = 0
    def read_utf():
        nonlocal off
        l = struct.unpack(">H", r[off:off+2])[0]; off += 2
        s = r[off:off+l]; off += l
        return s
    read_utf(); off += 8
    read_utf(); off += 8
    p_len = struct.unpack(">I", r[off:off+4])[0]; off += 4
    off += 8
    return r[off:off+p_len]

def generate_master_key(config):
    sb = []
    for key, always_str in MASTER_KEY_FIELDS:
        val = config.get(key)
        if always_str:
            if val is None: val = 0
            sb.append(py_str(val))
            continue
        if val is None: val = ""
        if py_truthy(val): sb.append(py_str(val))
    return hashlib.sha256("".join(sb).encode()).digest()

def clean_inner_fields(config, salt_key):
    cleaned = {}
    vital = {"overwriteServerData": True}
    for k, v in config.items():
        if isinstance(v, str) and v.strip() != "":
            try:
                d = decode_config_message(v) if k == "configMessage" else decrypt_xor_layer(v, salt_key)
                if d != "": cleaned[k] = d
                elif vital.get(k): cleaned[k] = v
            except Exception:
                if vital.get(k): cleaned[k] = v
        else:
            cleaned[k] = v
    return cleaned

def try_nested_json_parse(raw_str):
    s = raw_str.find("{"); e = raw_str.rfind("}")
    if s == -1 or e <= s: return None, False
    try:
        obj = json.loads(raw_str[s:e+1])
        if isinstance(obj, str):
            try: obj = json.loads(obj)
            except Exception: pass
        return obj, True
    except Exception:
        return None, False

def decrypt_ehi(file_bytes):
    payload = parse_ehi_bytes(file_bytes)
    if not payload: raise ValueError("failed parsing EHI structure")

    config = None; is_bypass = False
    for idx, iv in enumerate(allIVs):
        try:
            l1 = aes_cbc_decrypt(payload, L1Key, iv)
            parts = l1.decode('utf-8', errors='strict').split(":")
            if len(parts) < 3: continue
            iv2 = base64.b64decode(parts[0])
            garbage = aes_cbc_decrypt(base64.b64decode(parts[2]), L2KeyStatic, iv2)
            final_raw = xxtea_decrypt(garbage, EooMasterKey)
            start = final_raw.find(b"{")
            if start == -1: continue
            config = json.loads(final_raw[start:].decode('utf-8', errors='replace'))
            is_bypass = idx < len(SideIvs)
            break
        except Exception:
            continue

    if config is None: raise ValueError("decryption signature mismatch")

    target_salt = config.get("configSalt") or "EVZJNI"

    if is_bypass:
        parsed_final = config
    else:
        aaa = decrypt_xor_layer(config.get("configData", ""), target_salt)
        raw_payload = base64.b64decode(aaa)
        if len(raw_payload) <= 50: raise ValueError("malformed secondary raw payload")
        time_cost = struct.unpack("<I", raw_payload[1:5])[0]
        memory_cost = struct.unpack("<I", raw_payload[5:9])[0]
        parallelism = raw_payload[9]
        salt = raw_payload[0x0a:0x1a]
        nonce = raw_payload[0x1a:0x32]
        aad = raw_payload[:0x1a]
        master_key = generate_master_key(config)
        argon_key = argon2.low_level.hash_secret_raw(master_key, salt, time_cost, memory_cost, parallelism, 32, type=Type.ID)
        aead = ChaCha20_Poly1305.new(key=argon_key, nonce=nonce)
        aead.update(aad)
        plain = aead.decrypt_and_verify(raw_payload[0x32:-16], raw_payload[-16:])
        parsed_final = json.loads(plain.decode('utf-8', errors='replace'))

    cleaned = clean_inner_fields(parsed_final, target_salt)
    for field in ("v2rRawJson", "overwriteServerData"):
        raw_str = cleaned.get(field)
        if isinstance(raw_str, str):
            obj, ok = try_nested_json_parse(raw_str)
            if ok: cleaned[field] = obj
    return json.dumps(cleaned, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: ehi_full_decrypt.py <file.ehi> [out.json]", file=sys.stderr)
        sys.exit(2)
    with open(sys.argv[1], "rb") as f:
        data = f.read()
    result = decrypt_ehi(data)
    if len(sys.argv) > 2:
        with open(sys.argv[2], "w") as f:
            f.write(result)
    else:
        print(result)
