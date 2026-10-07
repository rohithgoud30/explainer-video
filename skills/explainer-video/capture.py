# /// script
# requires-python = ">=3.11"
# dependencies = ["playwright"]
# ///
"""Screenshot a source web page (docs, article, online book) for a slide.

Usage:
  capture.py URL OUT.png                         the article from its main title down
  capture.py URL OUT.png --section "Heading"     the section under the heading whose text contains "Heading"
  capture.py URL OUT.png --selector "CSS"        one element, e.g. "main pre" for the first code block

Options: --width 1280 (page width), --height (crop height; default 760 for a page, 16:10 for a section), --hide "CSS,CSS" (elements to remove,
e.g. cookie banners), --dark (ask the site for its dark theme).
Uses installed Google Chrome, or Playwright's Chromium if Chrome is missing.
"""
import argparse
import subprocess
import sys

from playwright.sync_api import sync_playwright

# Cookie and consent popups and ad slots that cover or clutter the content.
HIDE = ("[class*=cookie], [id*=cookie], [class*=consent], [id*=consent], [role=dialog], "
        "[class*=placement], [class*=advert], [id*=advert], ins.adsbygoogle, iframe[src*=ads]")

# Fixed and sticky bars (site headers, banners) float over whatever is scrolled under them; remove them.
UNSTICK_JS = """() => document.querySelectorAll('body *').forEach(e => {
  const p = getComputedStyle(e).position;
  if (p === 'fixed' || p === 'sticky') e.style.setProperty('display', 'none', 'important');
})"""

# Start the shot at a heading: the one whose text matches, or the page's main title when no text is given.
SECTION_JS = """([text, height]) => {
  const h = text
    ? [...document.querySelectorAll('h1, h2, h3, h4')].find(e => e.textContent.trim().toLowerCase().includes(text.toLowerCase()))
    : document.querySelector('main h1, article h1, h1');
  if (!h) return null;
  h.scrollIntoView({block: 'start'});
  const r = h.getBoundingClientRect();
  // Crop a section shot to its text column, so the words fill the frame instead of empty page margins.
  const col = text ? (h.closest('section, article, main') || document.body).getBoundingClientRect() : null;
  const x = col ? Math.max(0, col.left - 24) : 0;
  const width = col ? Math.min(col.width + 48, document.documentElement.clientWidth - x) : document.documentElement.clientWidth;
  // Slides are wide, so a section shot defaults to 16:10; a tall crop would shrink to fit and its text would be small.
  return {x, width, y: Math.max(0, r.top - 12) + window.scrollY, height: height || Math.round(width / 1.6)};
}"""


def main():
    ap = argparse.ArgumentParser(description="Screenshot a source page or one section of it.")
    ap.add_argument("url")
    ap.add_argument("out")
    ap.add_argument("--section", help="text of the heading to start the shot at")
    ap.add_argument("--selector", help="CSS selector of one element to shoot")
    ap.add_argument("--width", type=int, default=1280)
    ap.add_argument("--height", type=int, help="crop height (default: 760 for a page, 16:10 of the column for a section)")
    ap.add_argument("--hide", default="", help="extra CSS selectors to remove, comma separated")
    ap.add_argument("--dark", action="store_true")
    a = ap.parse_args()

    with sync_playwright() as pw:
        try:
            browser = pw.chromium.launch(channel="chrome")
        except Exception:
            subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
            browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": a.width, "height": a.height or 760}, device_scale_factor=2,
                                color_scheme="dark" if a.dark else "light")
        page.goto(a.url, wait_until="networkidle", timeout=60_000)
        hide = ", ".join(filter(None, [HIDE, a.hide]))
        page.add_style_tag(content=f"{hide} {{ display: none !important; }}")
        page.evaluate(UNSTICK_JS)
        # Lazy images only load when scrolled to; load them all so a section shot has no blank boxes.
        page.evaluate("() => document.querySelectorAll('img[loading=lazy]').forEach(i => i.loading = 'eager')")
        page.evaluate("async () => { for (let y = 0; y < document.body.scrollHeight; y += 600) {"
                      " window.scrollTo(0, y); await new Promise(r => setTimeout(r, 60)); } window.scrollTo(0, 0); }")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(500)

        if a.selector:
            page.locator(a.selector).first.screenshot(path=a.out)
        else:
            box = page.evaluate(SECTION_JS, [a.section or "", a.height or (0 if a.section else 760)])
            if box is None and a.section:
                sys.exit(f"No heading containing {a.section!r} on {a.url}")
            if box is None:  # no title on the page: shoot the top
                page.screenshot(path=a.out)
            else:
                page.screenshot(path=a.out, full_page=True,
                                clip={"x": box["x"], "y": box["y"], "width": box["width"], "height": box["height"]})
        browser.close()
    print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
