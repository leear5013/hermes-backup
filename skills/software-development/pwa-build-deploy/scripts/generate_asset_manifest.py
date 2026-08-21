#!/usr/bin/env python3
"""Generate BOOTSTRAP_CONFIG.assetManifest for a PWA served under a subpath.

Game engines with buildAssetUrl() resolve assets through BOOTSTRAP_CONFIG.assetManifest;
anything absent falls back to an ABSOLUTE '/path' URL which 404s under GitHub Pages
'/repo/' subpaths. This script maps every file in the PWA dir to a relative './' URL
under both bare and '/'-prefixed keys, then rewrites the assetManifest JSON inside
index.html in place.

Usage: python3 generate_asset_manifest.py /opt/work/frontwar-pwa
Re-run after adding any files (maps, icons, images). Then commit + push.
"""
import json, os, sys

def build_manifest(base):
    manifest = {}
    for root, dirs, files in os.walk(base):
        dirs[:] = [d for d in dirs if d not in ('.git', 'node_modules')]
        for f in files:
            rel = os.path.relpath(os.path.join(root, f), base).replace(os.sep, '/')
            manifest[rel] = './' + rel
            manifest['/' + rel] = './' + rel
    return manifest

def replace_manifest_in_html(html_path, manifest):
    s = open(html_path, encoding='utf-8').read()
    i = s.find('assetManifest: {')
    if i < 0:
        raise SystemExit('ERROR: "assetManifest: {" not found in ' + html_path)
    depth = 0; j = i + len('assetManifest: '); in_str = False; esc = False
    while j < len(s):
        c = s[j]
        if esc: esc = False
        elif c == '\\': esc = True
        elif c == '"': in_str = not in_str
        elif not in_str:
            if c == '{': depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0: break
        j += 1
    if depth != 0:
        raise SystemExit('ERROR: could not find matching close brace')
    s = s[:i] + 'assetManifest: ' + json.dumps(manifest) + s[j+1:]
    open(html_path, 'w', encoding='utf-8').write(s)

def main():
    base = sys.argv[1] if len(sys.argv) > 1 else '.'
    html = os.path.join(base, 'index.html')
    if not os.path.isfile(html):
        raise SystemExit('ERROR: no index.html in ' + base)
    manifest = build_manifest(base)
    replace_manifest_in_html(html, manifest)
    print(f'assetManifest rebuilt: {len(manifest)} entries written into {html}')

if __name__ == '__main__':
    main()
