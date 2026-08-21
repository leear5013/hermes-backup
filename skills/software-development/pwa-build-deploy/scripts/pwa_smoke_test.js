// pwa_smoke_test.js — production smoke test for a deployed PWA/game
// Usage: PLAYWRIGHT_BROWSERS_PATH=/opt/work/.pw-browsers node pwa_smoke_test.js <url> [--desktop] [customTag1 customTag2 ...]
// Checks: broken images, 4xx/5xx responses, undefined custom elements, page errors.
// Exit code: 0 clean, 1 failures found, 2 bad args. Writes screenshot to /tmp/pwa_smoke_<ts>.png
//
// WHY THIS EXISTS: every user-reported bug (unstyled UI, "?" placeholder icons,
// worker 404s) appeared ONLY against the live subpath + installed-SW conditions —
// localhost passes proved nothing. Run this against PRODUCTION after every deploy.

const args = process.argv.slice(2);
if (!args.length) {
  console.error("usage: node pwa_smoke_test.js <url> [--desktop] [tags...]");
  process.exit(2);
}
const url = args[0];
const desktop = args.includes("--desktop");
const extraTags = args.filter((a, i) => a !== url && a !== "--desktop" && i > 0);

const { chromium } = require("playwright");

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({
    viewport: desktop ? { width: 1280, height: 800 } : { width: 390, height: 844 },
  });
  const errors = [], missing = [];
  page.on("pageerror", (e) => errors.push(String(e).slice(0, 150)));
  page.on("response", (r) => {
    if (r.status() >= 400) missing.push(`${r.status()} ${r.url().slice(-60)}`);
  });

  await page.goto(url, { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForTimeout(4000);

  const result = await page.evaluate((extraTags) => {
    const brokenImgs = [];
    document.querySelectorAll("img").forEach((i) => {
      if (i.complete && i.naturalWidth === 0 && i.src) brokenImgs.push(i.src.slice(-60));
    });
    // default tag set from the FrontWar/OpenFront shell; pass extras to extend
    const tags = ["play-page","desktop-nav-bar","mobile-nav-bar","single-player-modal",
      "main-layout","win-modal","emoji-table","build-menu", ...extraTags];
    const undef = tags.filter((t) => !customElements.get(t));
    return { brokenImgs: [...new Set(brokenImgs)], undef };
  }, extraTags);

  await page.screenshot({ path: `/tmp/pwa_smoke_${Date.now()}.png` });

  let fail = 0;
  if (result.brokenImgs.length) { console.log("BROKEN IMAGES:"); result.brokenImgs.forEach(b => console.log("  ", b)); fail = 1; }
  else console.log("broken images: none");
  if (missing.length) { console.log("4xx/5xx:"); [...new Set(missing)].slice(0,15).forEach(m => console.log("  ", m)); fail = 1; }
  else console.log("4xx/5xx: none");
  if (result.undef.length) { console.log("UNDEFINED ELEMENTS:", result.undef); fail = 1; }
  else console.log("custom elements: all defined");
  const realErrs = errors.filter(e => !/Turnstile|Failed to fetch|gutter ads/.test(e));
  if (realErrs.length) { console.log("PAGE ERRORS:", realErrs.slice(0,5)); fail = 1; }
  else console.log("page errors: none");

  await browser.close();
  process.exit(fail);
})();
