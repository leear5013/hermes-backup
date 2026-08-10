#!/usr/bin/env python3
"""Extract the 7 Evozi obfuscation blobs from HTTP Injector Lite 5.3.1 in aput-object order.

Usage: python extract_lite_enc_strings.py <lite.apk> [outfile]
Default outfile: enc_strings.txt (one blob per line, UTF-8) — input for scripts/Deobf.java

Blob string-pool indices (Lite 5.3.1, exact <clinit> aput-object order):
59939, 59935, 59937, 59925, 59929, 59924, 59936  (lens 8191 x6 + 2355)
"""
import sys
import zipfile
import struct

def get_strings(dex_bytes):
    assert dex_bytes[:4] == b'dex\n'
    string_ids_size = struct.unpack_from('<I', dex_bytes, 0x38)[0]
    string_ids_off = struct.unpack_from('<I', dex_bytes, 0x3C)[0]
    strings = []
    for i in range(string_ids_size):
        off = struct.unpack_from('<I', dex_bytes, string_ids_off + i * 4)[0]
        pos = off
        while dex_bytes[pos] & 0x80:
            pos += 1
        pos += 1
        end = dex_bytes.find(b'\x00', pos)
        if end == -1:
            strings.append('')
            continue
        try:
            strings.append(dex_bytes[pos:end].decode('utf-8'))
        except UnicodeDecodeError:
            strings.append('')
    return strings

def main():
    apk_path = sys.argv[1] if len(sys.argv) > 1 else '/opt/work/ehi_lite531.apk'
    out_path = sys.argv[2] if len(sys.argv) > 2 else '/opt/work/enc_strings.txt'
    order = [59939, 59935, 59937, 59925, 59929, 59924, 59936]

    all_strings = []
    with zipfile.ZipFile(apk_path) as zf:
        for dn in [n for n in zf.namelist() if n.endswith('.dex')]:
            all_strings += get_strings(zf.read(dn))

    with open(out_path, 'w', encoding='utf-8') as f:
        for idx in order:
            f.write(all_strings[idx] + '\n')
    print('Written 7 blobs, lens:', [len(all_strings[i]) for i in order])

if __name__ == '__main__':
    main()
