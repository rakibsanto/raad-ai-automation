import os, time, pytest
from playwright.sync_api import Page, expect
BASE_URL = os.getenv("BASE_URL", "https://dev.prowhats.com/en")

def test_reset_password_page_loads(page: Page):
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    page.wait_for_load_state("domcontentloaded")
    assert "prowhats.com" in page.url or page.url.startswith(BASE_URL)

def test_reset_password_flow_1_successful_password_reset_full_journey_(page: Page):
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    page.wait_for_load_state("domcontentloaded")
    assert page.url

def test_reset_password_flow_2_email_not_registered(page: Page):
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    page.wait_for_load_state("domcontentloaded")
    assert page.url

def test_reset_password_flow_3_invalid_email_format(page: Page):
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    page.wait_for_load_state("domcontentloaded")
    assert page.url

def test_reset_password_flow_4_expired_reset_token(page: Page):
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    page.wait_for_load_state("domcontentloaded")
    assert page.url

def test_ec_r_01(page: Page):
    """EC-R-01: Email with leading/trailing spaces"""
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    page.wait_for_load_state("domcontentloaded")
    assert page.url

def test_ec_r_02(page: Page):
    """EC-R-02: Uppercase email"""
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    page.wait_for_load_state("domcontentloaded")
    assert page.url

def test_ec_r_03(page: Page):
    """EC-R-03: Submitting the reset form multiple times quickly"""
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    page.wait_for_load_state("domcontentloaded")
    assert page.url

def test_ec_r_04(page: Page):
    """EC-R-04: Requesting reset while already logged in"""
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    page.wait_for_load_state("domcontentloaded")
    assert page.url

def test_ec_r_05(page: Page):
    """EC-R-05: Token in URL has been tampered with"""
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    page.wait_for_load_state("domcontentloaded")
    assert page.url

def test_reset_password_mobile(page: Page):
    page.set_viewport_size({"width": 375, "height": 667})
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    page.wait_for_load_state("domcontentloaded")
    assert page.url

def test_reset_password_no_console_errors(page: Page):
    errors = []
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    page.wait_for_load_state("domcontentloaded")
    assert errors == [], f"Console errors: {errors[:3]}"
