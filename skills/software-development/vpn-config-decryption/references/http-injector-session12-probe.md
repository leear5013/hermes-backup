# HTTP Injector .ehi — full non-bypass pipeline VERIFIED (2026-08-10, session 12)

Follow-up to session-11 (`http-injector-session11-probe.md`): the Go-port MAC failure is
SOLVED. Both branches (bypass AND standard Argon2/ChaCha) now decrypt the same real file
("Turkcell TR 🔥.ehi", 22,408 B container / 22,368 B payload).

## What was wrong in the session-11 port

The port fed the AAD into `decrypt_and_verify()`'s TAG parameter:

```python
# WRONG (MAC check failed):
plain = aead.decrypt_and_verify(raw_payload[0x32:], aad)
```

`ChaCha20_Poly1305.decrypt_and_verify(ciphertext, received_mac_tag)` — the second arg is
the 16-byte Poly1305 tag, NOT the AAD. AAD must be fed first via `update()`:

```python
aead = ChaCha20_Poly1305.new(key=argon_key, nonce=nonce)
aead.update(aad)                                   # AAD = raw_payload[:0x1a]
plain = aead.decrypt_and_verify(raw_payload[0x32:-16], raw_payload[-16:])  # tag = last 16 B
```

The zhgddm `HTTPINJECTOR.py` module (lines ~233-235) shows exactly this shape.

## Verified end-to-end trace (real file, standard branch)

- IV loop: `StandardIvs[1]` (`522b01433a5e8b2fc7549e1ad368e541`) unpad-successes → `is_bypass=False`.
- L1 plaintext = `m2xVQsbZezmtMKx4IKS0Pg==:agyRNgQDJ/...:PfVr3mNVoh8v...` (3 colon parts).
- Outer config (19 keys): `configAesKey`, `configIdentifier`, `configSalt="bOS2fD"`,
  `configTimestamp`, `lockModes`, `lockModesHash`, `configData` (15,872 chars), ...
- xor layer: reverse → custom-b64 → hex → XOR with salt (`bOS2fD`) → drop 0x00 bytes.
- `base64.b64decode(xor_output)` → raw_payload header:
  `01 | 05000000 (time=5) | 00010000 (mem=65536 KiB) | 04 (p=4) | c0e37775… (salt 16B) | b51cd251… (nonce 24B) | ct | tag`
- master_key = SHA256(concat of 9 fields per session-11) → argon2id (5, 65536, 4) 32B.
- ChaCha20-Poly1305-X with 24B nonce + AAD=raw_payload[:0x1a] → inner JSON.
- Inner fields: `configMessage` via EHIMSG-UTF16BE XOR; other strings via xor-layer with
  the outer configSalt. Final JSON has `host`, `port`, `user`, `password`, `payload`,
  `remoteProxy`, `sniHostname`, `configMessage` (HTML promo), etc.

## configMessage decode — JAVA CHAR semantics (critical for Arabic/emoji)

The plaintext contains UTF-8 Arabic + emoji. Per-byte XOR (Go-faithful `[]rune` port) and
per-byte-with-replacement both produce mojibake. The working decode (from zhgddm module
`_decode_config_message`) treats it as Java chars:

```python
raw = base64.b64decode(padded)                      # padded to %4
utf16 = raw.decode('utf-8', errors='replace').encode('utf-16-be', errors='surrogatepass')
units = struct.unpack(f'>{len(utf16)//2}H', utf16)
xor = [u ^ ord("EHIMSG"[i % 6]) for i, u in enumerate(units)]
out = struct.pack(f'>{len(xor)}H', *xor).decode('utf-16-be', errors='surrogatepass')
result = out.encode('utf-16', 'surrogatepass').decode('utf-16')
```

Verified output contains clean emoji (`🌟VPS PREMIUM💥`) and Arabic (`مستو الحلبي`, `عبدو قيراطة`).

## Deliverable

`scripts/ehi_full_decrypt.py` — standalone CLI full-pipeline decryptor:
`/opt/venv/bin/python ehi_full_decrypt.py <file.ehi>` → clean config JSON to stdout.
Deps: pycryptodome + argon2-cffi (both in `/opt/venv`).

## Pitfalls hit this session

- **Sandbox reset wiped pycryptodome from /opt/venv** — reinstall with
  `/opt/venv/bin/pip install pycryptodome argon2-cffi -q` before running. (Not a skill
  bug; just reinstall.)
- **execute_code sandbox has NO pycryptodome** even when /opt/venv does — write the
  script to /opt/work and run with `/opt/venv/bin/python` via terminal.
- base64 with unpadded input → `binascii.Error: Incorrect padding` — pad with
  `"=" * ((4 - len % 4) % 4)` before decode.
- File uploads with emoji/space filenames (`doc_2f4feb518070_Turkcell TR 🔥.ehi`) break
  shell globbing — copy via Python `shutil.copy` to an ASCII path.
- archive.org old APKs: `com.evozi.injector` (2017, 5.5MB) = pre-cloud, no key;
  `http-injector-v-5.3.1-size-12326324_202103` (2021) = cloud-era strings but still no
  `CONFIG_AES_KEY` value — the gap to hunt is **5.3.1 < v < 6.4.1**.
