import os
from playwright.sync_api import sync_playwright

BASE_URL = os.getenv("BASE_URL", "https://dev.prowhats.com/en")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(BASE_URL)
    page.wait_for_timeout(3000)
    
    inputs = page.locator("input").all()
    for i, inp in enumerate(inputs):
        try:
            print(f"[{i}] INPUT type={inp.get_attribute('type')} | name={inp.get_attribute('name')} | placeholder={inp.get_attribute('placeholder')}")
        except Exception:
            pass
    browser.close()
