#!/usr/bin/env python3
"""Dump function symbols from a Go Android .so (pclntab walk), no Go toolchain needed.

Usage:
    /opt/venv/bin/python go-pclntab-symbols.py libgojni.so [filter-substring]

Works on Go >=1.18 32-bit (armeabi-v7a) .so. Prints "vaddr  name" for every function
whose name contains the filter (or all if no filter). Then map vaddr→file offset via
ELF LOAD segments for disassembly, and resolve pc-rel literals:
    ldr rX,[pc,#imm]  -> literal at (ins_addr + 8 + imm)
    add rX, pc, rX    -> rX = (add_addr + 8) + literal_value
"""
import struct, sys

data = open(sys.argv[1], 'rb').read()
filt = sys.argv[2].encode() if len(sys.argv) > 2 else b''

pch = data.find(b'\xf1\xff\xff\xff')
if pch == -1:
    print("no Go pcHeader magic (0xFFFFFFF1) found — not a Go .so?"); sys.exit(1)
print(f"pcHeader @ 0x{pch:x}")

nfunc   = struct.unpack_from('<I', data, pch + 8)[0]
textst  = struct.unpack_from('<I', data, pch + 16)[0]
fn_off  = struct.unpack_from('<I', data, pch + 20)[0]
pcln_off = struct.unpack_from('<I', data, pch + 36)[0]
print(f"nfunc={nfunc} textStart=0x{textst:x} funcnameOffset={fn_off:#x} pclnOffset={pcln_off:#x}")

functab = pch + 40
namebase = pch + fn_off
pclnbase = pch + pcln_off

def walk_aligned():
    """Scan 4-byte-aligned positions in pclntab; treat each as a _func candidate.
    This was the method that actually found everything androguard-style misses."""
    seen = {}
    pos = pclnbase
    end = len(data) - 16
    while pos < end:
        nameoff = struct.unpack_from('<i', data, pos + 4)[0]
        entryoff = struct.unpack_from('<I', data, pos)[0]
        nameaddr = namebase + nameoff
        if 0 <= nameaddr < len(data) - 200:
            nb = data[nameaddr]
            if 0x20 <= nb < 0x7f:
                endn = data.find(b'\x00', nameaddr, nameaddr + 200)
                if endn != -1:
                    name = data[nameaddr:endn]
                    if filt in name:
                        seen.setdefault(name, textst + entryoff)
        pos += 4
    return seen

def walk_functab():
    """Direct functab walk (may miss entries if offsets misalign; kept for reference)."""
    seen = {}
    for i in range(nfunc):
        entryoff = struct.unpack_from('<I', data, functab + i*8)[0]
        funcoff  = struct.unpack_from('<I', data, functab + i*8 + 4)[0]
        foff = pclnbase + funcoff
        if foff + 8 > len(data): continue
        no = struct.unpack_from('<i', data, foff + 4)[0]
        nameaddr = namebase + no
        end = data.find(b'\x00', nameaddr, nameaddr + 300)
        if end == -1 or end - nameaddr > 300: continue
        name = data[nameaddr:end]
        if filt in name:
            seen.setdefault(name, textst + entryoff)
    return seen

hits = walk_aligned()
if not hits:
    hits = walk_functab()
for name, addr in sorted(hits.items()):
    print(f"0x{addr:08x}  {name.decode('ascii', 'replace')}")
print(f"--- {len(hits)} symbols ---")
