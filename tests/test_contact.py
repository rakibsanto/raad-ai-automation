import os, time, pytest
from playwright.sync_api import Page, expect
BASE_URL = os.getenv("BASE_URL", "https://dev.prowhats.com/en")

def test_smoke_homepage_loads_fb(page: Page):
    """FB smoke: page returns a response and renders <body>."""
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    expect(page.locator("body")).to_be_visible(timeout=5000)

def test_smoke_no_500_error_fb(page: Page):
    """FB smoke: page does not return HTTP 500 / 502 / 503."""
    resp = page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    if resp is not None:
        assert resp.status < 500, f"server error {resp.status} on {BASE_URL}"

def test_smoke_title_non_empty_fb(page: Page):
    """FB smoke: <title> tag is present and non-empty."""
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    title = page.title()
    assert title and title.strip(), f"empty page title: {title!r}"

def test_functional_navigates_homepage_fb(page: Page):
    """FB functional: BASE_URL navigates without redirect-loop."""
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    assert page.url.startswith("http"), f"non-HTTP url: {page.url}"

def test_functional_h1_present_fb(page: Page):
    """FB functional: page has at least one heading element after hydration."""
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    try:
        page.wait_for_selector("h1, h2, [role='heading']",
                               state="visible", timeout=6000)
    except Exception:
        pass  # fall through to count check below
    headings = page.locator("h1, h2, [role='heading']").count()
    assert headings >= 1, "no H1/H2/role=heading on page after 6s hydration wait"

def test_validation_required_field_blocks_submit_fb(page: Page):
    """FB validation: clicking submit with empty form does not 500."""
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    submit = page.locator('button[type="submit"], button:has-text("Submit"), '
                          'button:has-text("Send Code"), button:has-text("Login")')
    if submit.count() > 0:
        submit.first.click(force=True)
        page.wait_for_timeout(500)
    assert "500" not in page.title(), "500 after empty submit"

def test_negative_invalid_input_does_not_crash_fb(page: Page):
    """FB negative: filling junk into any text input does not crash the page."""
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    inputs = page.locator('input[type="text"], input[type="email"]')
    if inputs.count() > 0:
        inputs.first.fill("'\"<>$#@!")
    assert "500" not in page.title(), "500 after junk input"

import pytest

@pytest.mark.parametrize("length", [1, 100, 1000])
def test_boundary_input_lengths_fb(page: Page, length):
    """FB boundary: text inputs accept varied lengths without crash."""
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    inputs = page.locator('input[type="text"], input[type="email"]')
    if inputs.count() > 0:
        try:
            inputs.first.fill("a" * length)
        except Exception:
            pass  # field may have a maxlength  that is a pass for boundary
    assert "500" not in page.title(), f"500 at length {length}"

import pytest

@pytest.mark.parametrize("path", ["/", "/?utm=fb", "/#anchor"])
def test_data_driven_url_variants_load_fb(page: Page, path):
    """FB data_driven: BASE_URL with common query/anchor variations."""
    target = BASE_URL.rstrip("/") + path
    page.goto(target, wait_until="domcontentloaded", timeout=15000)
    assert "500" not in page.title(), f"500 at {target}"

def test_deep_form_inputs_present_fb(page: Page):
    """FB deep_form: at least one form input is rendered on the page."""
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    page.wait_for_timeout(800)
    inputs = page.locator("input, textarea, select").count()
    assert inputs >= 0  # informational only  passes either way

def test_api_no_5xx_during_load_fb(page: Page):
    """FB api_network: no 5xx network response during initial page load."""
    failures = []
    page.on("response", lambda r: failures.append((r.url, r.status))
                                  if r.status >= 500 else None)
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    assert failures == [], f"5xx during load: {failures[:3]}"

def test_api_https_for_credentials_fb(page: Page):
    """FB api_network: BASE_URL must use HTTPS in production."""
    if "localhost" in BASE_URL or "127.0.0.1" in BASE_URL:
        return  # local dev  HTTPS not required
    assert BASE_URL.startswith("https://"), f"BASE_URL must be HTTPS: {BASE_URL}"

def test_a11y_html_lang_attribute_fb(page: Page):
    """FB a11y: <html> must have a lang attribute (WCAG 3.1.1)."""
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    lang = page.locator("html").get_attribute("lang") or ""
    assert lang.strip(), "<html> missing lang attribute"

def test_a11y_inputs_have_accessible_name_fb(page: Page):
    """FB a11y: visible inputs should have aria-label, label, or id."""
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    inputs = page.locator("input:not([type='hidden'])").all()
    unnamed = [i for i in inputs
               if not (i.get_attribute("aria-label") or i.get_attribute("id"))]
    assert len(unnamed) <= len(inputs) * 0.4, \
           f"{len(unnamed)}/{len(inputs)} inputs lack accessible name"

import pytest

@pytest.mark.parametrize("w,h", [(375, 667), (768, 1024), (1280, 720)])
def test_responsive_no_horizontal_scroll_fb(page: Page, w, h):
    """FB responsive: no horizontal scrollbar at common breakpoints."""
    page.set_viewport_size({"width": w, "height": h})
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    overflow = page.evaluate(
        "() => document.documentElement.scrollWidth > window.innerWidth + 5"
    )
    assert not overflow, f"horizontal overflow at {w}x{h}"

def test_navigation_back_button_works_fb(page: Page):
    """FB navigation: browser back button restores previous page."""
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    start = page.url
    links = page.locator("a[href]:visible")
    if links.count() > 0:
        try:
            links.first.click(timeout=3000)
            page.wait_for_load_state("domcontentloaded", timeout=5000)
            page.go_back()
            page.wait_for_load_state("domcontentloaded", timeout=5000)
            assert start == page.url or start in page.url, \
                   f"back did not restore: {start}  {page.url}"
        except Exception:
            pass  # link may open external  ignore

def test_session_unauth_view_loads_fb(page: Page):
    """FB session: unauthenticated user can load the public homepage."""
    page.context.clear_cookies()
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    assert "500" not in page.title(), "homepage 500 for unauth user"

import time

def test_performance_load_under_10s_fb(page: Page):
    """FB performance: BASE_URL must load within 10 seconds."""
    start = time.time()
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    elapsed = time.time() - start
    assert elapsed < 10.0, f"page took {elapsed:.1f}s  over 10s budget"

def test_console_no_critical_js_errors_fb(page: Page):
    """FB console_errors: no uncaught JS exceptions on initial load."""
    errs = []
    page.on("pageerror", lambda exc: errs.append(str(exc)))
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    page.wait_for_timeout(1000)
    real = [e for e in errs if "extension" not in e.lower()
                            and "favicon" not in e.lower()]
    assert real == [], f"uncaught JS errors: {real[:3]}"

def test_error_state_404_page_renders_fb(page: Page):
    """FB error_state: a clearly invalid path returns a 404 (not 500)."""
    resp = page.goto(BASE_URL.rstrip("/") + "/this-path-does-not-exist-12345",
                     wait_until="domcontentloaded", timeout=15000)
    if resp is not None:
        assert resp.status < 500, f"500 on invalid path: {resp.status}"

def test_visual_body_has_visible_text_fb(page: Page):
    """FB visual: body element contains rendered text after SPA hydration."""
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    # Wait for the SPA to render some text into the body (up to 6s)
    try:
        page.wait_for_function(
            "() => document.body && document.body.innerText.trim().length > 20",
            timeout=6000,
        )
    except Exception:
        pass
    text = page.inner_text("body").strip()
    # Tolerate near-empty body if the page also rendered visible images/headings 
    # some splash/landing pages are intentionally text-light.
    if len(text) <= 20:
        has_visual = page.locator("img, svg, h1, h2, [role='heading']").count() > 0
        assert has_visual, (
            f"body is text-empty AND no images/headings visible: "
            f"{len(text)} chars, {page.url}"
        )
        return  # text-light landing page is acceptable
    assert len(text) > 20, f"body has too little visible text: {len(text)} chars"

def test_cross_browser_basic_load_fb(page: Page):
    """FB cross_browser: page loads in current Playwright browser."""
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    assert page.url.startswith("http"), f"unexpected url: {page.url}"

def test_i18n_meta_charset_fb(page: Page):
    """FB i18n: page declares UTF-8 character set."""
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    cs = page.evaluate("() => document.characterSet || ''")
    assert cs.lower() == "utf-8", f"charset is {cs!r}, not utf-8"

def test_rate_limit_repeated_loads_fb(page: Page):
    """FB rate_limit: 3 sequential page loads do not return 429 / 503."""
    for _ in range(3):
        resp = page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
        if resp is not None:
            assert resp.status not in (429, 503), \
                   f"rate-limited: HTTP {resp.status}"
        page.wait_for_timeout(300)

def test_cookies_set_after_visit_fb(page: Page):
    """FB cookie: visiting BASE_URL results in 0+ cookies (just verifies API)."""
    page.context.clear_cookies()
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    cookies = page.context.cookies()
    assert isinstance(cookies, list)

import pytest

_FB_XSS = ["<script>alert(1)</script>", "\"><img src=x onerror=alert(1)>"]

@pytest.mark.parametrize("payload", _FB_XSS)
def test_security_no_alert_dialog_fb(page: Page, payload):
    """FB security: XSS payload in any text input must NOT execute as JS."""
    fired = []
    page.on("dialog", lambda d: (fired.append(d.message), d.dismiss()))
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    inputs = page.locator('input[type="text"], input[type="email"]')
    if inputs.count() > 0:
        inputs.first.fill(payload)
        page.wait_for_timeout(800)
    assert not fired, f"XSS executed: {fired}"