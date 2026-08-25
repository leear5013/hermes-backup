#!/usr/bin/env python3
"""Live duty ticker — no GitHub, no app installs.

Serves TODAY + TOMORROW on the local network as a live HTML page:
  iPhone Safari -> http://<host>:<port> -> Share -> Add to Home Screen.
The schedule alternates S/H forever from a start date; no re-imports ever.

Usage: python3 duty_ticker.py [port]
"""
import datetime, sys
from http.server import BaseHTTPRequestHandler, HTTPServer

START = datetime.date(2026, 8, 24)  # Monday = Seif's turn

def owner(d):
    return "S" if (d - START).days % 2 == 0 else "H"

def owner_name(o):
    return "Seif" if o == "S" else "Hesham"

def render():
    today = datetime.date.today()
    t, n = owner(today), owner(today + datetime.timedelta(days=1))
    return (f"<meta charset='utf-8'><meta name='viewport' content='width=device-width'>"
            f"<style>body{{background:#000;color:#fff;font-family:-apple-system,sans-serif;"
            f"display:flex;flex-direction:column;justify-content:center;align-items:center;"
            f"height:100vh;margin:0;text-align:center}}"
            f".today{{font-size:64px;font-weight:800}} .who{{font-size:120px;font-weight:900;color:#39d353}}"
            f".tom{{font-size:28px;color:#999;margin-top:12px}} .big{{font-size:40px}}</style>"
            f"<div class='today'>TODAY</div>"
            f"<div class='who'>{t} — {owner_name(t)}'s turn</div>"
            f"<div class='tom big'>Tomorrow: {n} — {owner_name(n)}'s turn</div>")

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        body = render().encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def log_message(self, *a): pass

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8123
    print(f"Duty ticker live on http://0.0.0.0:{port}")
    HTTPServer(("0.0.0.0", port), H).serve_forever()
