#!/usr/bin/env bash
# tls-sni-probe.sh — probe whether a host+port terminates TLS itself on raw TCP
# (i.e. whether a "fake SNI" vless/vmess link can work against it).
#
# The fake-SNI DPI-evasion pattern (sni=<innocent-host>&allowInsecure=1) only
# works when the SERVER terminates TLS directly on the port you connect to:
#   - server ignores the ClientHello SNI and presents its OWN cert (any CN)
#   - the client forgives the mismatch via insecure=1/allowInsecure=1
# An HTTPS edge proxy (Railway default, Cloudflare, etc.) validates SNI and
# REJECTS a foreign SNI before your app ever sees the bytes -> fake-SNI fails.
#
# Usage:
#   tls-sni-probe.sh <host> <port> [fake-sni] [real-sni]
#   tls-sni-probe.sh gr1.vpnjantit.com 10002 mab.etisalat.com.eg gr1.vpnjantit.com
#
# Exit 0 if BOTH handshakes succeed (fake-SNI viable). Non-zero otherwise.
# Only needs openssl. Output is printed to stdout; the harness-friendly
# caller can `2>/dev/null` or write output to a file (harness truncates piped
# stdout hard — prefer writing probe output to a FILE and reading it).

set -u
HOST="${1:?usage: tls-sni-probe.sh <host> <port> [fake-sni] [real-sni]}"
PORT="${2:?usage: tls-sni-probe.sh <host> <port> [fake-sni] [real-sni]}"
FAKE_SNI="${3:-$HOST}"
REAL_SNI="${4:-$HOST}"

echo "=== fake SNI: $FAKE_SNI @ $HOST:$PORT ==="
echo | timeout 20 openssl s_client -connect "$HOST:$PORT" -servername "$FAKE_SNI" -brief 2>&1 | head -8
echo
echo "=== real SNI: $REAL_SNI @ $HOST:$PORT ==="
echo | timeout 20 openssl s_client -connect "$HOST:$PORT" -servername "$REAL_SNI" -brief 2>&1 | head -8
echo

if echo | timeout 20 openssl s_client -connect "$HOST:$PORT" -servername "$FAKE_SNI" 2>/dev/null >/dev/null; then
    echo "RESULT: fake-SNI handshake SUCCEEDS -> server terminates TLS itself; fake-SNI link viable here."
    exit 0
else
    echo "RESULT: fake-SNI handshake FAILS -> SNI is validated (edge proxy / strict server); use real-SNI TLS or TCP-proxy + self-signed."
    exit 1
fi