# PWA Smoke Test Script

Run against the **LIVE URL** after every deploy. Requires Playwright with browsers at `PLAYWRIGHT_BROWSERS_PATH=/opt/work/.pw-browsers`.

```python
#!/usr/bin/env python3
"""Production smoke test for FrontWar PWA.
Run: python3 scripts/pwa_smoke_test.js https://leear5013.github.io/frontwar2/
"""

import sys
import asyncio
from playwright.async_api import async_playwright

async def smoke_test(url: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 390, "height": 844},  # iPhone 13
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15"
        )
        page = await context.new_page()
        
        errors = []
        responses_4xx = []
        broken_images = []
        
        page.on("console", lambda msg: print(f"  [console] {msg.text[:200]}"))
        page.on("pageerror", lambda err: errors.append(str(err)))
        page.on("response", lambda resp: responses_4xx.append(resp.url) if resp.status >= 400 else None)
        
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        
        # Check custom elements
        custom_tags = await page.evaluate("""() => {
            const tags = new Set();
            document.querySelectorAll("*").forEach(el => {
                if (el.tagName.includes("-")) tags.add(el.tagName.toLowerCase());
            });
            return Array.from(tags);
        }""")
        undefined_elements = []
        for tag in custom_tags:
            defined = await page.evaluate(f"() => customElements.get('{tag}') !== undefined")
            if not defined:
                undefined_elements.append(tag)
        
        # Check images
        broken_images = await page.evaluate("""() => {
            return Array.from(document.querySelectorAll("img"))
                .filter(img => !img.complete || img.naturalWidth === 0)
                .map(img => img.src || img.getAttribute("src") || "?");
        }""")
        
        # Try solo flow
        await page.evaluate("() => { const b=Array.from(document.querySelectorAll('button')).find(x=>x.innerText.trim()==='Solo'); b?.click(); }")
        await page.wait_for_timeout(2000)
        await page.wait_for_url("**#modal=single-player", timeout=10000)
        await page.wait_for_timeout(1000)
        
        await page.evaluate("""() => {
            const all = document.querySelectorAll('*');
            const starts = Array.from(all).filter(el => 
                el.textContent && el.textContent.toLowerCase().includes('start game') && 
                (el.tagName === 'BUTTON' || el.tagName === 'O-BUTTON' || el.getAttribute('role') === 'button')
            );
            if (starts.length > 0) starts[0].click();
        }""")
        
        # Wait for map load
        await page.wait_for_timeout(15000)
        
        # Check if game started
        map_loaded = await page.evaluate("""() => {
            return window.__MAP_LOADED__ === true;
        }""")
        
        await browser.close()
        
        print(f"\n=== SMOKE TEST RESULTS for {url} ===")
        print(f"Custom elements found: {len(custom_tags)}")
        print(f"Undefined custom elements: {undefined_elements}")
        print(f"Broken images: {len(broken_images)}")
        for img in broken_images[:10]:
            print(f"  {img}")
        print(f"4xx responses: {len(responses_4xx)}")
        for resp in responses_4xx[:10]:
            print(f"  {resp}")
        print(f"Page errors: {len(errors)}")
        for err in errors[:5]:
            print(f"  {err[:200]}")
        print(f"Map loaded flag: {map_loaded}")
        
        success = (len(undefined_elements) == 0 and 
                   len(broken_images) == 0 and 
                   len(responses_4xx) == 0 and 
                   len(errors) == 0)
        print(f"\nOVERALL: {'PASS' if success else 'FAIL'}")
        return success

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "https://leear5013.github.io/frontwar2/"
    ok = asyncio.run(smoke_test(url))
    sys.exit(0 if ok else 1)
```