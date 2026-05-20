import os
from playwright.sync_api import sync_playwright

BASE_URL = os.getenv("BASE_URL", "https://dev.prowhats.com/en")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(BASE_URL)
    page.wait_for_timeout(3000)
    
    buttons = page.locator("button, a").all()
    for i, b in enumerate(buttons):
        try:
            text = b.inner_text().strip()
            print(f"[{i}] {b.evaluate('el => el.tagName')} | {text} | href: {b.get_attribute('href')} | aria-label: {b.get_attribute('aria-label')}")
        except Exception:
            pass
    browser.close()
