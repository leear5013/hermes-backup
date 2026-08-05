---
name: html-to-image
description: Use when rendering HTML to PNG images for Telegram.
---

# HTML → Image Rendering

Pillow/PIL cannot render color emoji (Noto Color Emoji uses CBDT bitmap format). Always use **Chromium headless** for any HTML that needs emoji, fonts, or accurate rendering.

## Chromium headless command
```bash
chromium --headless --no-sandbox --disable-gpu \
  --screenshot=output.png --window-size=1200,900 \
  "file://$(pwd)/page.html"
```
- `--no-sandbox` required in Docker/root environments
- `--window-size=W,H` controls viewport (and thus screenshot dimensions)
- dbus errors in stderr are harmless — ignore them
- Output: `output.png` in current directory

## Workflow
1. Write self-contained HTML (inline CSS, Google Fonts via CDN are fine)
2. Render with Chromium headless
3. Send via `MEDIA:/path/to/output.png`

## Pitfalls
- Pillow's `ImageFont` + `ImageDraw` cannot render emoji — never use for emoji-containing visuals
- If Chromium is not installed: `apt-get install -y chromium`
- `wkhtmltoimage` is NOT available in Debian 13 repos — don't waste time looking for it
- For simple shapes without emoji, Pillow is fine and faster
