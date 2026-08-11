#!/data/data/com.termux/files/usr/bin/bash
# ============================================================
#  SNI WHITELIST TEST — Egypt quota-exhaustion bypass
#  RUN THIS WHEN YOUR DATA = 0% (quota consumed) — that's the
#  ONLY time the ISP whitelist filter is active!
#  Install deps first:  pkg install -y openssl-tool curl
# ============================================================

# Your Railway proxy (change if you redeploy)
PROXY="sakura.proxy.rlwy.net:14210"

SNIS="www.mod.gov.eg www.parliament.gov.eg mcit.gov.eg mped.gov.eg www.moee.gov.eg \
www.investinegypt.gov.eg www.gafi.gov.eg scu.eg www.egyptconsulates.org moe.gov.eg \
mof.gov.eg www.manpower.gov.eg enationality.moi.gov.eg digital.gov.eg psm.gov.eg \
www.civilaviation.gov.eg ar.awkafonline.com islamic-council.net www.dar-alifta.org \
www.moc.gov.eg www.emys.gov.eg mohesr.gov.eg www.nccm.gov.eg www.capmas.gov.eg \
www.idsc.gov.eg www.mohp.gov.eg moa.gov.eg elpai.idsc.gov.eg traffic.moi.gov.eg \
eservice.incometax.gov.eg egfwd.com ekb.eg emis.gov.eg maharatech.gov.eg \
www.mlzamty.com www.nagwa.com speedtest.net"

if [ ! -x "$(command -v openssl)" ]; then pkg update -y && pkg install -y openssl-tool curl; fi

echo ""
echo "================ TEST 1: SNI passes your ISP DPI? ================"
echo "(TLS handshake with that SNI name to your proxy, through YOUR net)"
echo "PASS = DPI let it through -> usable as sni= in your vless link"
echo "================================================================"
PASSED=""
for sni in $SNIS; do
  if timeout 8 openssl s_client -connect "$PROXY" -servername "$sni" -brief </dev/null >/dev/null 2>&1; then
    echo "  ✅ PASS   $sni"
    PASSED="$PASSED $sni"
  else
    echo "  ❌ FAIL   $sni"
  fi
done

echo ""
echo "================ TEST 2: real site browsable at 0%? =============="
echo "(direct curl to the real domain — whitelist depth check)"
echo "HTTP 200 = site itself whitelisted (best camouflage)"
echo "================================================================"
for sni in $SNIS; do
  code=$(timeout 8 curl -s -o /dev/null -w "%{http_code}" "https://$sni" 2>/dev/null)
  echo "  $code   $sni"
done

echo ""
echo "================ RESULT ========================================"
echo "SNIs that PASSED the DPI handshake:"
for sni in $PASSED; do echo "  ✔ $sni"; done
echo ""
echo "PICK RULE: prefer .gov.eg domains that ALSO returned HTTP 200"
echo "in TEST 2. Swap one into your link: sni=<domain>&host=<domain>"
echo "================================================================"