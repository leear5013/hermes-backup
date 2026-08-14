# ssh:// and nm-vless:// / nm-vmess:// decode (reusable recipe)

Verified live 2026-08-13. These three share schemes all reduce to the SAME
NetMod AES-128-ECB + PKCS7 3-key try-loop; only the *output shape* differs.

## The 3 keys (in try order)
```python
NM_KEYS = [b"<n3t5yn4^n3tm0d>", b"_netsyna_netmod_", b"nicetrybuddygoon"]
```
NOTE: `<n3t5yn4^n3tm0d>` — `n3t5yn4` is the digit 4, NOT a caret. base64 of the
literal bytes is `PG4zdDV5bjRebjN0bTBkPg==`.

## Generic NetMod blob decrypt
```python
from Crypto.Cipher import AES
import base64

def decrypt_netmod(payload_b64):
    blob = base64.b64decode(payload_b64 + "=" * (-len(payload_b64) % 4))
    if len(blob) % 16 != 0:
        raise ValueError("ciphertext not block-aligned")
    for key in NM_KEYS:
        dec = AES.new(key, AES.MODE_ECB).decrypt(blob)
        pad = dec[-1]
        if 1 <= pad <= 16 and dec[-pad:] == bytes([pad]) * pad:
            return dec[:-pad], key
    raise ValueError("no NetMod key matched")
```

## nm-vmess:// -> JSON
```python
plain, key = decrypt_netmod(code)        # code = text after "nm-vmess://"
obj = json.loads(plain)                   # vmess config JSON
```

## nm-vless:// -> vless URI string (do NOT json.loads)
```python
plain, key = decrypt_netmod(code)        # code = text after "nm-vless://"
vless_uri = plain.decode("utf-8")         # e.g. 164245b8-...@www.nagwa.com:8443?security=tls&...
```
VERIFIED: key `_netsyna_netmod_` decrypted a real nm-vless into
`164245b8-3d39-...@www.nagwa.com:8443?security=tls&encryption=none&headerType=none&type=ws&path=%252Frealtime&flow=none&host=www.nagwa.com.khartosh.dpdns.org&fp=chrome&sni=...#raise and install router اتصلات`

## ssh:// -> plaintext URI fields + optional encrypted payload
Format: `ssh://<user>:<pass>@<host>:<port>?u+<base64>=<front-host:port@front-user:front-pass>`
- `<user>:<pass>@<host>:<port>` before `?` = REAL SSH server creds.
- `u+<base64>` = NetMod AES blob (same 3-key scheme) -> `json.loads` SSH config JSON.
- The `=` after base64 is the **fragment separator** (`#`-style), NOT padding.
- Fragment = proxy front: `host:port@user:pass` (usually an Egyptian whitelisted host).

```python
import urllib.parse, re

def decode_ssh(uri):
    p = urllib.parse.urlparse(uri)
    netloc = p.netloc
    user, hostport = (netloc.split("@", 1) + [""])[:2] if "@" in netloc else ("", netloc)
    ssh_user, ssh_pass = (user.split(":", 1) + [""])[:2] if ":" in user else (user, "")
    host, port = (hostport.rsplit(":", 1) + [""])[:2] if ":" in hostport else (hostport, "")
    frag = urllib.parse.unquote(p.fragment)
    proxy = ""
    if frag:
        ph, pu = (frag.split("@", 1) + [""])[:2] if "@" in frag else (frag, "")
        proxy = f"proxy host: {ph}\nproxy cred: {pu}"
    lines = [f"ssh host: {host}", f"ssh port: {port}",
             f"ssh user: {ssh_user}", f"ssh pass: {ssh_pass}"]
    if proxy:
        lines.append(proxy)
    q = urllib.parse.unquote(p.query)
    if q.startswith("u+"):
        b64 = q[2:].split("=", 1)[0]          # strip fragment sep
        try:
            data = re.sub(r"[^A-Za-z0-9+/=]", "", b64).rstrip("=")
            blob = base64.b64decode(data + "=" * (-len(data) % 4))
            if len(blob) % 16 == 0:
                for key in NM_KEYS:
                    dec = AES.new(key, AES.MODE_ECB).decrypt(blob)
                    pad = dec[-1]
                    if 1 <= pad <= 16 and dec[-pad:] == bytes([pad]) * pad:
                        lines.append("payload (key `{}`):".format(key.decode()))
                        lines.append(dec[:-pad].decode("utf-8", errors="replace"))
                        break
                else:
                    lines.append("payload: [no NetMod key matched] raw: " + b64)
            else:
                lines.append("payload: [not block-aligned] raw: " + b64)
        except Exception as e:
            lines.append("payload: [decode error {}]".format(type(e).__name__))
    return "```\n" + "\n".join(lines) + "\n```"
```

## PITFALL — pasted ssh:// base64 corruption
When the user pastes an `ssh://` link inline (Telegram/shell), a `+` or `=` gets
mangled -> base64 length off by 1, decode fails. Always:
1. Strip the fragment: `b64 = query[2:].split("=", 1)[0]`
2. Sanitize: `re.sub(r"[^A-Za-z0-9+/=]", "", b64).rstrip("=")`
3. Re-pad: `base64.b64decode(b64 + "=" * (-len(b64) % 4))`
4. If still not mod16, the paste is corrupt -> return plaintext fields + raw base64, don't crash.
BEST PRACTICE: ask the user to send the link inside a `.txt` file -- files preserve
`+`/`=` exactly and the payload decrypts cleanly.
