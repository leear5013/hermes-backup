#!/usr/bin/env python3
"""Probe fake-SNI candidates against a VLESS/WSS Railway TCP proxy.

Two-part test:
  1. TLS handshake to PROXY_HOST:PROXY_PORT with -servername <candidate>
     (server must accept the fake SNI — all do when the edge is a raw TCP proxy).
  2. HTTPS HEAD to the REAL domain (liveness: DPI sees a resolvable, serving name).

Usage:
    python sni_probe.py                        # default list + default proxy
    python sni_probe.py proxy.host 14210       # override proxy
Edit SNIS below to test your own candidates.
Requires: stdlib only. ~36 SNIs in ~30s (12 threads).
"""
import socket, ssl, urllib.request, concurrent.futures, datetime, sys

PROXY_HOST = sys.argv[1] if len(sys.argv) > 1 else "sakura.proxy.rlwy.net"
PROXY_PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 14210

SNIS = [
    "speedtest.net",
    "www.mod.gov.eg", "www.parliament.gov.eg", "mcit.gov.eg", "mped.gov.eg",
    "www.moee.gov.eg", "www.investinegypt.gov.eg", "www.gafi.gov.eg", "scu.eg",
    "www.egyptconsulates.org", "moe.gov.eg", "mof.gov.eg", "www.manpower.gov.eg",
    "enationality.moi.gov.eg", "digital.gov.eg", "psm.gov.eg", "www.civilaviation.gov.eg",
    "ar.awkafonline.com", "islamic-council.net", "www.dar-alifta.org", "www.moc.gov.eg",
    "www.emys.gov.eg", "mohesr.gov.eg", "www.nccm.gov.eg", "www.capmas.gov.eg",
    "www.idsc.gov.eg", "www.mohp.gov.eg", "moa.gov.eg", "elpai.idsc.gov.eg",
    "traffic.moi.gov.eg", "eservice.incometax.gov.eg", "egfwd.com", "ekb.eg",
    "emis.gov.eg", "maharatech.gov.eg", "www.mlzamty.com", "www.nagwa.com",
]

def resolve(host):
    try:
        infos = socket.getaddrinfo(host, 443, socket.AF_INET, socket.SOCK_STREAM)
        return sorted({i[4][0] for i in infos})[:3]
    except Exception:
        return None

def proxy_tls_handshake(sni):
    try:
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with socket.create_connection((PROXY_HOST, PROXY_PORT), timeout=8) as sock:
            with ctx.wrap_socket(sock, server_hostname=sni) as tls:
                cert = tls.getpeercert()
                cn = None
                if cert:
                    for rdn in cert.get("subject", ()):
                        for k, v in rdn:
                            if k == "commonName":
                                cn = v
                return {"ok": True, "tls": tls.version(), "cert_cn": cn}
    except Exception as e:
        return {"ok": False, "err": str(e)[:60]}

def live_https(host):
    try:
        req = urllib.request.Request(f"https://{host}/", method="HEAD",
                                     headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=7) as r:
            return f"HTTP {r.status}"
    except Exception as e:
        return str(e)[:50]

def test_one(sni):
    ip = resolve(sni)
    hs = proxy_tls_handshake(sni)
    live = live_https(sni) if ip else "no-dns"
    return {"sni": sni, "dns": ",".join(ip) if ip else "FAIL",
            "hs": "OK" if hs["ok"] else "FAIL",
            "tls": hs.get("tls", ""), "cn": hs.get("cert_cn", "") or hs.get("err", ""),
            "live": live}

results = []
with concurrent.futures.ThreadPoolExecutor(max_workers=12) as ex:
    for r in ex.map(test_one, SNIS):
        results.append(r)

results.sort(key=lambda r: (r["hs"] != "OK", not bool(r["dns"])))
print(f"=== SNI probe: {PROXY_HOST}:{PROXY_PORT} @ {datetime.datetime.utcnow().isoformat()}Z ===")
for r in results:
    print(f"{r['sni']:<32} {r['dns']:<22} HS={r['hs']:<4} {r['tls']:<8} cert:{r['cn'][:20]:<22} live:{r['live']}")