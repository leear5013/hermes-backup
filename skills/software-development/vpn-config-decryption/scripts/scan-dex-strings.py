#!/usr/bin/env python3
"""Scan Android APK/XAPK dex bytes for strings WITHOUT java/jadx/apktool/strings.

Works on this VPS (no java, no jadx, no `strings` binary). Extracts every
classes*.dex from the APK (or XAPK → inner APK), pulls printable ASCII runs,
filters against regex patterns, dedupes. Keys/markers in obfuscated Kotlin/Go
apps are plain strings in the dex — this finds them.

Usage:
    python3 scan-dex-strings.py <app.apk|app.xapk> [pattern1 pattern2 ...]
    # default patterns cover the tunnel-app family (netmod, aes, vmess, nm-, ...)

Exit code 0 always; findings on stdout. For XAPK (zip of split APKs), the
main app APK is the one whose name ends in .apk and contains classes.dex
(typically the biggest; config.armeabi_v7a.apk holds the native .so libs).
"""
import re
import sys
import zipfile

DEFAULT_PATTERNS = [
    rb'(?i)(aes|netsyna|netmod|cipher|secret|encrypt|decrypt|password|passwd|key)',
    rb'(?i)(vmess|vless|trojan|socks|ssh|ssr|dns|wireguard|xray|nm-)',
    rb'nm-[a-z]+://',
]

MIN_LEN = 4  # 16-byte keys and markers are comfortably above this; low catches short flags


def iter_dex_bytes(apk_path):
    """Yield (dex_name, bytes) for every classes*.dex found in an APK or XAPK."""
    with zipfile.ZipFile(apk_path) as z:
        for name in z.namelist():
            if name.endswith('.dex'):
                yield name, z.read(name)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    apk_path = sys.argv[1]
    pats = [re.compile(p.encode() if isinstance(p, str) else p) for p in sys.argv[2:]] or DEFAULT_PATTERNS

    found_any = False
    for dex_name, data in iter_dex_bytes(apk_path):
        strings = re.findall(rb'[ -~]{%d,}' % MIN_LEN, data)
        hits = [s for s in strings if any(p.search(s) for p in pats)]
        if not hits:
            continue
        found_any = True
        print(f'=== {dex_name}: {len(strings)} strings, {len(hits)} hits ===')
        seen = set()
        for h in hits:
            hh = h[:150]
            if hh in seen:
                continue
            seen.add(hh)
            print('  ', hh.decode('utf-8', 'replace'))
    if not found_any:
        print('no hits in any classes*.dex')


if __name__ == '__main__':
    main()
