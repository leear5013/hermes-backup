# ============================================================
#  REAL SNI TUNNEL TEST (Windows PowerShell) — E2E byte flow
#  The ONLY SNI test that counts against stateful/destination
#  filters: spins up a REAL xray VLESS client per SNI (same
#  params as the user's working phone link), pushes REAL
#  traffic through the proxy, PASS = HTTP 200 on egress.
#
#  USE: powershell -ExecutionPolicy Bypass -File sni_tunnel_test.ps1 [-Quick]
#  NEEDS: xray.exe (auto-detects v2rayN's bundled one, else put
#  xray-windows-64.exe from https://github.com/XTLS/Xray-core/releases
#  next to this script). + curl.exe (built into Win10/11).
#  RULE: run at 0% QUOTA — whitelists only activate when quota is exhausted.
# ============================================================
param([switch]$Quick)

# ---- EDIT: these must match the user's working deployment ----
$ProxyHost = "sakura.proxy.rlwy.net"
$ProxyPort = 14210
$UUID = "3d921ec4-cd73-4aa4-bc7c-2113ac70158e"
$Path  = "/fhxkzop4vbll"
$CertPin = "976B8A8AD8B1A0750C656E0DF65C734C6FFC09BDF2C835F93D8E13AE03AEF616"
$TestURL = "http://example.com/"   # egress probe; 200 = bytes flowed through the tunnel
# ------------------------------------------------------------

# Known-good SNI FIRST = positive control. If THIS fails, the harness
# is broken (params wrong / xray missing), not the SNI list.
$SNIs = @(
  "speedtest.net",
  "www.mod.gov.eg","www.parliament.gov.eg","mcit.gov.eg","mped.gov.eg",
  "www.moee.gov.eg","www.investinegypt.gov.eg","www.gafi.gov.eg","scu.eg",
  "www.egyptconsulates.org","moe.gov.eg","mof.gov.eg","www.manpower.gov.eg",
  "enationality.moi.gov.eg","digital.gov.eg","psm.gov.eg","www.civilaviation.gov.eg",
  "ar.awkafonline.com","islamic-council.net","www.dar-alifta.org","www.moc.gov.eg",
  "www.emys.gov.eg","mohesr.gov.eg","www.nccm.gov.eg","www.capmas.gov.eg",
  "www.idsc.gov.eg","www.mohp.gov.eg","moa.gov.eg","elpai.idsc.gov.eg",
  "traffic.moi.gov.eg","eservice.incometax.gov.eg","egfwd.com","ekb.eg",
  "emis.gov.eg","maharatech.gov.eg","www.mlzamty.com","www.nagwa.com"
)
if ($Quick) { $SNIs = $SNIs | Select-Object -First 10 }

$Xray = $null
$searchPaths = @(
  "$env:LOCALAPPDATA\Programs\v2rayN\bin\xray\xray.exe",
  "$env:USERPROFILE\Downloads\xray.exe",
  "C:\xray\xray.exe",
  "$PSScriptRoot\xray.exe"
)
foreach ($p in $searchPaths) { if (Test-Path $p) { $Xray = $p; break } }
if (-not $Xray) {
  $Xray = "$PSScriptRoot\xray.exe"
  if (-not (Test-Path $Xray)) {
    Write-Host "xray.exe not found. Download BEFORE quota hits 0%:" -ForegroundColor Yellow
    Write-Host "  1) https://github.com/XTLS/Xray-core/releases" -ForegroundColor Cyan
    Write-Host "  2) grab xray-windows-64.zip, extract, put xray.exe next to this script" -ForegroundColor Cyan
    exit 1
  }
}
Write-Host "Using xray: $Xray" -ForegroundColor Green

$script:testNo = 0
function Test-Sni($sni) {
  $script:testNo++
  $port = 10800 + $script:testNo
  $cfg = "$env:TEMP\sni_$script:testNo.json"
  $json = @"
{
  "log": {"loglevel": "error"},
  "inbounds": [{"port": $port, "listen": "127.0.0.1", "protocol": "socks",
    "settings": {"udp": true}}],
  "outbounds": [{
    "protocol": "vless",
    "settings": {"vnext": [{"address": "$ProxyHost", "port": $ProxyPort,
      "users": [{"id": "$UUID", "encryption": "none"}]}]},
    "streamSettings": {"network": "ws", "security": "tls",
      "tlsSettings": {"serverName": "$sni", "fingerprint": "chrome",
        "pinnedPeerCertSha256": "$CertPin"},
      "wsSettings": {"path": "$Path", "headers": {"Host": "$sni"}}}
  }]
}
"@
  Set-Content -Path $cfg -Value $json -Encoding Ascii
  $proc = Start-Process -FilePath $Xray -ArgumentList "run -c `"$cfg`"" -PassThru -WindowStyle Hidden
  Start-Sleep -Milliseconds 1500
  $code = $null
  try {
    $code = & curl.exe -s -o NUL -w "%{http_code}" -m 8 --socks5-hostname 127.0.0.1:$port $TestURL 2>$null
  } catch { $code = $null }
  if ($proc -and -not $proc.HasExited) { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue }
  Remove-Item $cfg -ErrorAction SilentlyContinue
  [PSCustomObject]@{ SNI = $sni; Code = $code; Pass = ($code -eq "200") }
}

Write-Host ""
Write-Host "=== REAL TUNNEL TEST: $($SNIs.Count) SNIs @ $ProxyHost:$ProxyPort ===" -ForegroundColor Cyan
Write-Host "=== egress: $TestURL (200 = bytes flowed) | RUN AT 0% QUOTA ===" -ForegroundColor Cyan
Write-Host ""
$Passed = @()
foreach ($sni in $SNIs) {
  $r = Test-Sni $sni
  $status = if ($r.Pass) { "PASS  " } else { "FAIL  " }
  $color = if ($r.Pass) { "Green" } else { "Red" }
  Write-Host ("  {0} {1,-32} HTTP {2}" -f $status, $r.SNI, $r.Code) -ForegroundColor $color
  if ($r.Pass) { $Passed += $r.SNI }
}

Write-Host ""
Write-Host "=== WINNERS (real tunnel works at 0%): ===" -ForegroundColor Cyan
if ($Passed.Count -eq 0) {
  Write-Host "  NONE — destination IP (proxy) is blocked at 0%; SNI can't fix that." -ForegroundColor Yellow
} else {
  $Passed | ForEach-Object { Write-Host "  $($_)" -ForegroundColor Green }
  Write-Host ""
  Write-Host "Put the FIRST winner into your vless link:" -ForegroundColor Green
  $w = $Passed[0]
  Write-Host "vless://$UUID@$ProxyHost`:$ProxyPort?encryption=none&security=tls&sni=$w&allowInsecure=1&fp=chrome&type=ws&host=$w&path=$Path#my-railway-vpn" -ForegroundColor White
}
Write-Host "Done."