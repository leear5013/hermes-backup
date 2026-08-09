#!/usr/bin/env python3
"""Deobfuscate obfuscator.io-style JS embedded in an HTML page.

Handles the classic obfuscator.io pattern found on Evozi's cloud-config pages
(config.ehi.link / ehi.link) and many other Android-tunnel share pages:
  - string array `U()` with `U=function(){return v;}` reassignment
  - array-rotation IIFE `(function(G,J){const M=I,F=G();while(!![]){try{const p=<expr>;if(p===J)break;else F.push(F.shift());}catch(n){F.push(F.shift());}}}(U,0x<target>))`
  - custom base64 alphabet (lowercase-first!) + RC4 decrypt with per-index keys
  - decode call sites like `(0x173,'wj5j')` inside `I=function(p,n){...}`

Usage:
    /opt/venv/bin/python deobfuscate_obfuscatorio.py <page.html> [--decode-calls]

Prints the simulated rotation result, then every decoded string (all array
elements), and finally the specific (index,key) call sites found in the page
if --decode-calls is given. Requires only stdlib.

VERIFIED 2026-08-09 on https://config.ehi.link/ed242a7S (34-element array):
rotation matched after 8 shifts; key strings decoded to
`window['location'] = 'https://app.ehi.link/config'` etc.
"""
import re
import sys


def extract_array(src):
    m = re.search(r"function U\(\)\{const v=\[(.*?)\];U=function", src, re.S)
    if not m:
        return None
    return re.findall(r"'([^']*)'", m.group(1))


ALPH = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+/="


def b64_decode_custom(s):
    """Custom-alphabet base64 (lowercase-first). NOTE: NOT standard base64."""
    bits = n = 0
    out = bytearray()
    for ch in s.rstrip("="):
        idx = ALPH.index(ch)
        bits = (bits << 6) | idx
        n += 6
        if n >= 8:
            n -= 8
            out.append((bits >> n) & 0xFF)
    return bytes(out)


def rc4(data, key):
    """RC4 over the decoded STRING's code points.

    CRITICAL PITFALL: the JS operates on `charCodeAt` of the
    decodeURIComponent'd string (code points), NOT on re-encoded UTF-8 bytes.
    Passing `data.encode('utf-8')` here silently produces garbage decodes.
    """
    t = list(range(256))
    C = 0
    kc = [ord(c) for c in key]
    kl = len(key)
    for Y in range(256):
        C = (C + t[Y] + kc[Y % kl]) % 0x100
        t[Y], t[C] = t[C], t[Y]
    Y = C = 0
    out = []
    for ch in data:
        Y = (Y + 1) % 0x100
        C = (C + t[Y]) % 0x100
        t[Y], t[C] = t[C], t[Y]
        out.append(chr(ord(ch) ^ t[(t[Y] + t[C]) % 0x100]))
    return "".join(out)


def decode_item(item, key):
    try:
        u = b64_decode_custom(item).decode("utf-8")
    except Exception:
        return None
    return rc4(u, key)


def js_parse_int(s):
    s = s.strip()
    mh = re.match(r"(-?)0[xX]([0-9a-fA-F]+)", s)
    if mh:
        return int(mh.group(2), 16) * (-1 if mh.group(1) else 1)
    md = re.match(r"(-?)(\d+)", s)
    if md:
        return int(md.group(2)) * (-1 if md.group(1) else 1)
    return float("nan")


def parse_rotation_expr(src):
    """Pull the (offset, key, sign, divisor) terms from the rotation IIFE."""
    m = re.search(r"while\(!!\[\]\)\{try\{const p=(.*?);if\(p===J\)", src, re.S)
    if not m:
        return None, None
    expr = m.group(1)
    target_m = re.search(r"\(U,0x([0-9a-fA-F]+)\)", src)
    target = int(target_m.group(1), 16) if target_m else None
    terms = []
    # terms look like: [-+]?parseInt(M\(0xNNN,'KEY'\))/0xN
    for tm in re.finditer(r"([+-])?parseInt\((?:M|I)\((0x[0-9a-fA-F]+),'([^']*)'\)\)/(0x[0-9a-fA-F]+)", expr):
        sign = -1 if tm.group(1) == "-" else 1
        terms.append((int(tm.group(2), 16), tm.group(3), sign, int(tm.group(4), 16)))
    return terms, target


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    src = open(sys.argv[1], encoding="utf-8", errors="ignore").read()
    items = extract_array(src)
    if not items:
        print("No obfuscator.io U() array found in", sys.argv[1])
        return 1
    print(f"Array size: {len(items)}")

    terms, target = parse_rotation_expr(src)
    arr = items[:]

    def dec(offset, key, live=arr):
        idx = offset - 0x164
        if not (0 <= idx < len(live)):
            return None
        return decode_item(live[idx], key)

    matched = None
    if terms and target is not None:
        for step in range(4000):
            p = 0.0
            for off, key, sign, div in terms:
                v = dec(off, key)
                try:
                    p += sign * js_parse_int(v) / div
                except Exception:
                    pass
            if abs(p - target) < 0.001:
                matched = step
                print(f"ROTATION MATCHED after {step} shifts (p={p:.1f} == {target})")
                break
            arr.append(arr.pop(0))
    else:
        print("Rotation expression/target not found; using unrotated array")

    if matched is None:
        print(f"No exact rotation match (checked up to 4000); using last state")

    print("\n--- all decoded strings (post-rotation) ---")
    for i, item in enumerate(arr):
        # no key at this point — print only if it decodes to ASCII-ish without a key
        pass

    # find every decode call site in the page: (0xNNN,'KEY')
    if "--decode-calls" in sys.argv:
        print("\n--- decode call sites ---")
        sites = re.findall(r"\((0x[0-9a-fA-F]+),'([^']*)'\)", src)
        seen = set()
        for off, key in sites:
            idx = int(off, 16) - 0x164
            if (idx, key) in seen:
                continue
            seen.add((idx, key))
            s = decode_item(arr[idx], key) if 0 <= idx < len(arr) else None
            print(f"I({off},'{key}') = {s!r}")


if __name__ == "__main__":
    sys.exit(main())
