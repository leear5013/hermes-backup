#!/usr/bin/env python3
"""Zero-dependency Telegram config-decrypt bot (stdlib only).

Drop the 5 decryptor modules (NPVTUNNEL.py, HTTPCUSTOM.py, HTTPINJECTOR.py,
DARKTUNNEL.py, SSCCUSTOM.py from github.com/zhgddm/npv-) into ./decryptors,
then run:

    BOT_TOKEN=<token> python3 decrypt_bot.py

Upload a config file (.npvt .npv4 .inpv .npv .hc .hjson .ehi .dt .ssc .txt)
and it replies with the decrypted JSON. Nothing redacted.
Paste a share link (vmess:// vless:// trojan:// ss:// nm-vmess://) and it
decodes it inline. Only /start is special-cased; everything else text goes
through decode_share_link.

v4 (2026-08-08): all decodes are wrapped in ```json / ``` code fences so they
render as clean blocks on Telegram (user preference). Encrypted nm-vmess
payloads are detected (AES-block fingerprint) and reported honestly instead of
crashing with a UnicodeDecodeError. See ../references/nm-vmess-format.md.
"""
import base64
import importlib.util
import json
import logging
import os
import re
import sys
import time
import urllib.parse
import urllib.request

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("decryptbot")

DECRYPTORS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "decryptors")
MAX_MSG = 4096

DECRYPTOR_MAP = {
    ".npvt": ("NPVTUNNEL.py", "NPV Tunnel"),
    ".npv4": ("NPVTUNNEL.py", "NPV Tunnel"),
    ".inpv": ("NPVTUNNEL.py", "NPV Tunnel"),
    ".npv":  ("NPVTUNNEL.py", "NPV Tunnel"),
    ".hc":   ("HTTPCUSTOM.py", "HTTP Custom"),
    ".hjson":("HTTPCUSTOM.py", "HTTP Custom"),
    ".ehi":  ("HTTPINJECTOR.py", "HTTP Injector"),
    ".dt":   ("DARKTUNNEL.py", "Dark Tunnel"),
    ".ssc":  ("SSCCUSTOM.py", "SSC Custom"),
    ".txt":  None,  # sniff content
}

_loaded = {}


def load_decryptor(module_file):
    if module_file in _loaded:
        return _loaded[module_file]
    path = os.path.join(DECRYPTORS_DIR, module_file)
    spec = importlib.util.spec_from_file_location(module_file.replace(".", "_"), path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _loaded[module_file] = mod
    return mod


def sniff_and_run(data: bytes):
    for module_file in ("NPVTUNNEL.py", "HTTPCUSTOM.py", "HTTPINJECTOR.py",
                        "DARKTUNNEL.py", "SSCCUSTOM.py"):
        try:
            mod = load_decryptor(module_file)
            res = mod.run(data) if hasattr(mod, "run") else None
            if res:
                return module_file, res
        except Exception as e:
            log.warning("sniff %s: %s", module_file, e)
    return None, None


def decrypt(data: bytes, ext: str):
    if ext not in DECRYPTOR_MAP or DECRYPTOR_MAP[ext] is None:
        return sniff_and_run(data)
    module_file = DECRYPTOR_MAP[ext][0]
    mod = load_decryptor(module_file)
    return mod.run(data), module_file


def strip_watermark(res):
    """Cut the decryptors' wrapper (header + '====' + 'code : @...' footer) down to the JSON."""
    if res and "{" in res and "}" in res:
        return res[res.find("{"):res.rfind("}") + 1]
    return res


def _json_block(obj):
    """Pretty JSON inside a ```json fence (user preference for Telegram rendering)."""
    return "```json\n" + json.dumps(obj, indent=2, ensure_ascii=False) + "\n```"


def _fence(text):
    """Plain-text block inside a ``` fence."""
    return "```\n" + text + "\n```"


def decode_share_link(text):
    """Decode vmess:// (base64 JSON), nm-vmess://, ss://, vless://, trojan:// found in text."""
    out = []
    found = False
    for m in re.finditer(r'(vmess|vless|trojan|ss|nm-vmess)://[^\s]+', text):
        found = True
        scheme, payload = m.group(0).split('://', 1)
        payload = payload.strip().strip('`').strip(')').strip('>')
        try:
            raw = base64.b64decode(payload + "=" * (-len(payload) % 4))
            if scheme in ("vmess", "nm-vmess"):
                if raw[:1] in (b"{", b"\xef"):  # '{' or UTF-8 BOM → plain JSON path
                    out.append(f"🔓 {scheme}:// decoded:\n" + _json_block(json.loads(raw)))
                else:
                    # AES-encrypted nm-vmess (272 B = 17×16 blocks fingerprint) — honest report
                    out.append(f"🔒 {scheme}:// is ENCRYPTED (not base64 JSON): {len(raw)} bytes, "
                               f"first byte 0x{raw[0]:02x}, mod16={len(raw) % 16}.\n"
                               "Key/schema not cracked yet — needs NetMod APK analysis.")
            elif scheme == "ss":
                # ss://base64(method:password)@host:port#name
                name = ""
                if "#" in payload:
                    payload, name = payload.split("#", 1)
                if "@" in payload:
                    b64part, netloc = payload.split("@", 1)
                    cred = base64.b64decode(b64part + "=" * (-len(b64part) % 4)).decode(errors="replace")
                    out.append(f"🔓 ss:// decoded:\n" + _fence(f"server: {netloc}\ncredentials: {cred}\nname: {name}"))
                else:
                    dec = base64.b64decode(payload + "=" * (-len(payload) % 4)).decode(errors="replace")
                    out.append(f"🔓 ss:// decoded:\n" + _fence(f"{dec}\nname: {name}"))
            elif scheme in ("vless", "trojan"):
                p = urllib.parse.urlparse(m.group(0))
                hostport = p.netloc or ""
                if "@" in hostport:
                    uid, hostport = hostport.split("@", 1)
                else:
                    uid = ""
                q = urllib.parse.parse_qs(p.query)
                lines = [f"uuid/psw: {uid}", f"server: {hostport}"]
                lines += [f"{k}: {v[0]}" for k, v in q.items()]
                if p.fragment:
                    lines.append(f"name: {urllib.parse.unquote(p.fragment)}")
                out.append(f"🔓 {scheme}:// decoded:\n" + _fence("\n".join(lines)))
        except Exception as e:
            out.append(f"❌ {scheme}:// decode failed ({type(e).__name__}): {e}")
    return "\n\n".join(out), found


def handle_text(chat_id, text):
    result, found = decode_share_link(text)
    if found:
        for part in split_text(result):
            api("sendMessage", chat_id=chat_id, text=part)


def _token():
    return os.environ.get("BOT_TOKEN") or sys.argv[1]


def api(method, **params):
    url = f"https://api.telegram.org/bot{_token()}/{method}"
    req = urllib.request.Request(url, data=urllib.parse.urlencode(params).encode())
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode())


def split_text(text, limit=MAX_MSG):
    if len(text) <= limit:
        return [text]
    parts, cur = [], ""
    for line in text.split("\n"):
        if len(cur) + len(line) + 1 > limit:
            parts.append(cur)
            cur = line
        else:
            cur = cur + "\n" + line if cur else line
    if cur:
        parts.append(cur)
    return parts


def get_updates(offset, timeout=50):
    q = urllib.parse.urlencode({"offset": offset, "timeout": timeout})
    req = urllib.request.Request(f"https://api.telegram.org/bot{_token()}/getUpdates?" + q)
    with urllib.request.urlopen(req, timeout=timeout + 15) as resp:
        return json.loads(resp.read().decode())


def handle_document(chat_id, file_id, file_name, file_size):
    try:
        with urllib.request.urlopen(
                f"https://api.telegram.org/bot{_token()}/getFile?file_id={file_id}",
                timeout=30) as resp:
            fdata = json.loads(resp.read().decode())
        if not fdata.get("ok"):
            api("sendMessage", chat_id=chat_id,
                text=f"❌ getFile failed: {fdata.get('description', 'unknown')}")
            return
        fpath = fdata["result"]["file_path"]
        with urllib.request.urlopen(
                f"https://api.telegram.org/file/bot{_token()}/{fpath}",
                timeout=60) as resp:
            data = resp.read()
        ext = os.path.splitext(file_name or "")[1].lower()
        log.info("decrypt chat=%s file=%s ext=%s bytes=%s", chat_id, file_name, ext, len(data))

        res, module_file = decrypt(data, ext)
        if not res:
            api("sendMessage", chat_id=chat_id,
                text=f"❌ Could not decrypt `{file_name}` — unknown/unsupported format.\n\n"
                     "Supported: .npvt .npv4 .inpv .npv .hc .hjson .ehi .dt .ssc (.txt auto-sniff).")
            return
        label = DECRYPTOR_MAP[ext][1] if ext in DECRYPTOR_MAP and DECRYPTOR_MAP[ext] else "auto"
        res = strip_watermark(res)  # clean JSON, same shape as share-link decodes (user pref)
        header = f"🔓 Decrypted `{file_name}` ({label})\n"
        body = "```json\n" + res + "\n```" if res else res
        for part in split_text(header + body):
            api("sendMessage", chat_id=chat_id, text=part)
    except Exception as e:
        log.exception("handle_document error")
        try:
            api("sendMessage", chat_id=chat_id, text=f"❌ Error: {type(e).__name__}: {e}")
        except Exception:
            pass


def main():
    if not (os.environ.get("BOT_TOKEN") or len(sys.argv) > 1):
        print("usage: python3 decrypt_bot.py <BOT_TOKEN>", file=sys.stderr)
        sys.exit(1)
    log.info("bot starting...")
    offset = 0
    while True:
        try:
            upd = get_updates(offset)
            if not upd.get("ok"):
                time.sleep(3)
                continue
            for u in upd.get("result", []):
                offset = u["update_id"] + 1
                msg = u.get("message") or u.get("edited_message")
                if not msg:
                    continue
                chat_id = msg["chat"]["id"]
                doc = msg.get("document")
                if doc:
                    handle_document(chat_id, doc["file_id"],
                                    doc.get("file_name", "file.bin"),
                                    doc.get("file_size", 0))
                elif msg.get("text"):
                    # /start is special-cased; any other text is scanned for share links.
                    if msg["text"] == "/start":
                        api("sendMessage", chat_id=chat_id,
                            text="👋 Send any config file and I'll decrypt it:\n"
                                 "`.npvt` `.npv4` `.inpv` `.npv` (NPV Tunnel)\n"
                                 "`.hc` `.hjson` (HTTP Custom)\n"
                                 "`.ehi` (HTTP Injector)\n"
                                 "`.dt` (Dark Tunnel) `.ssc` (SSC Custom)\n\n"
                                 "Or paste a `vmess://` `vless://` `trojan://` `ss://` "
                                 "`nm-vmess://` code and I'll decode it.\n\n"
                                 "Raw output, nothing redacted. 🔓")
                    else:
                        handle_text(chat_id, msg["text"])
        except Exception as e:
            log.error("poll error: %s", e)
            time.sleep(3)


if __name__ == "__main__":
    main()
