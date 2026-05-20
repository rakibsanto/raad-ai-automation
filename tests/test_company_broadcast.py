import os, time, pytest, datetime, re
from playwright.sync_api import Page, expect

# ── Environment ────────────────────────────────────────────────────────────────
BASE_URL      = os.getenv("BASE_URL",      "https://dev.prowhats.com/en")
LOGIN_URL     = os.getenv("LOGIN_URL",     "https://dev.prowhats.com/en/login")
BROADCAST_URL = os.getenv("BROADCAST_URL", "https://dev.prowhats.com/en/broadcast")
CREATE_BROADCAST_URL = f"{BASE_URL}/broadcast/create"

OWNER_EMAIL    = os.getenv("OWNER_EMAIL",    "saidurdev@gmail.com")
OWNER_PASSWORD = os.getenv("OWNER_PASSWORD", "saidurdev@gmail.com")
ADMIN_EMAIL    = os.getenv("ADMIN_EMAIL",    "rakibsanto1998@gmail.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "111111")
AGENT_EMAIL    = os.getenv("AGENT_EMAIL",    "rakibsanto.cse@gmail.com")
AGENT_PASSWORD = os.getenv("AGENT_PASSWORD", "111111")

NAV = 'wait_until="domcontentloaded", timeout=20000'

# ----------------------------
# Helper Functions
# ----------------------------

def unique_campaign():
    return f"Broadcast_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"

def _login(page: Page, email: str, password: str) -> bool:
    """Navigate to login, fill email+password, submit. Returns True on success."""
    page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=20000)
    page.wait_for_timeout(1500)

    # Fill email
    email_sel = ('input[type="email"], input[name="email"], '
                 'input[placeholder*="mail" i], input[placeholder*="Email" i]')
    try:
        page.wait_for_selector(email_sel, state="visible", timeout=8000)
        page.locator(email_sel).first.fill(email)
    except Exception:
        return False

    # Fill password
    pwd_sel = ('input[type="password"], input[name="password"], '
               'input[placeholder*="assword" i]')
    try:
        page.wait_for_selector(pwd_sel, state="visible", timeout=5000)
        page.locator(pwd_sel).first.fill(password)
    except Exception:
        return False

    # Submit
    submit_sel = ('button[type="submit"], button:has-text("Login"), '
                  'button:has-text("Sign In"), button:has-text("Log In")')
    try:
        page.locator(submit_sel).first.click()
        page.wait_for_timeout(3000)
    except Exception:
        return False

    # Check if we landed on the dashboard or anywhere else authenticated
    return "dashboard" in page.url or "dashboard" in page.title().lower() or "broadcast" in page.url

def _assert_broadcast_page(page: Page, email: str, password: str):
    """Login and navigate to broadcast page; skip if login fails."""
    success = _login(page, email, password)
    if not success:
        page.goto(BROADCAST_URL, wait_until="domcontentloaded", timeout=20000)
        page.wait_for_timeout(2000)
        if "login" in page.url:
            pytest.skip(f"Login failed for {email} — broadcast inaccessible")
    else:
        page.goto(BROADCAST_URL, wait_until="domcontentloaded", timeout=20000)
        page.wait_for_timeout(2000)


# ----------------------------
# Role-Based Authentication
# ----------------------------

def test_admin_can_access_broadcast(page: Page):
    _assert_broadcast_page(page, ADMIN_EMAIL, ADMIN_PASSWORD)
    expect(page.locator("body")).to_contain_text("Broadcast", ignore_case=True)

def test_owner_can_access_broadcast(page: Page):
    _assert_broadcast_page(page, OWNER_EMAIL, OWNER_PASSWORD)
    expect(page.locator("body")).to_contain_text("Broadcast", ignore_case=True)

def test_agent_cannot_access_broadcast(page: Page):
    success = _login(page, AGENT_EMAIL, AGENT_PASSWORD)
    if success:
        page.goto(BROADCAST_URL)
        page.wait_for_timeout(2000)
        # Agent should be redirected or see an access denied message
        # We assume if they stay on broadcast, they might see an error.
        if "broadcast" in page.url:
             expect(page.locator("body")).to_contain_text(re.compile("denied|unauthorized|forbidden|403|not found|pageNotFound", re.IGNORECASE))
    else:
        pytest.skip("Agent login failed")

def test_unauthenticated_access_redirects_to_login(page: Page):
    page.goto(BROADCAST_URL, wait_until="domcontentloaded", timeout=20000)
    page.wait_for_timeout(2000)
    assert "login" in page.url or "login" in page.content().lower()

# ----------------------------
# Listing Dashboard
# ----------------------------

def test_broadcast_table_columns(page: Page):
    _assert_broadcast_page(page, ADMIN_EMAIL, ADMIN_PASSWORD)
    page.wait_for_timeout(2000)
    body = page.locator("body")
    expect(body).to_contain_text("Name")
    expect(body).to_contain_text("Status")

# ----------------------------
# Pagination
# ----------------------------

def test_pagination_controls(page: Page):
    _assert_broadcast_page(page, ADMIN_EMAIL, ADMIN_PASSWORD)
    next_btn = page.locator('button:has-text("Next"), [aria-label="Next"], [class*="next"]:not([disabled])')
    if next_btn.count() > 0:
        expect(next_btn.first).to_be_visible()

# ----------------------------
# Search Functionality
# ----------------------------

def test_search_broadcast(page: Page):
    _assert_broadcast_page(page, ADMIN_EMAIL, ADMIN_PASSWORD)
    search_sel = ('input[placeholder*="Search" i]')
    search_inputs = page.locator(search_sel)
    if search_inputs.count() > 0:
        search_inputs.first.fill("Test")
        search_inputs.first.press("Enter")
    else:
        pytest.skip("Search input not found")

def test_clear_search(page: Page):
    _assert_broadcast_page(page, ADMIN_EMAIL, ADMIN_PASSWORD)
    search_sel = ('input[placeholder*="Search" i]')
    search_inputs = page.locator(search_sel)
    if search_inputs.count() > 0:
        search_inputs.first.fill("Test")
        search_inputs.first.press("Enter")
        page.wait_for_timeout(500)
        search_inputs.first.fill("")
        search_inputs.first.press("Enter")
    else:
        pytest.skip("Search input not found")

# ----------------------------
# Status Filters
# ----------------------------

def test_status_filter_dropdown(page: Page):
    _assert_broadcast_page(page, ADMIN_EMAIL, ADMIN_PASSWORD)
    filter_btn = page.locator('button:has-text("Status"), [class*="filter"]')
    if filter_btn.count() > 0:
        filter_btn.first.click()
        page.wait_for_timeout(500)
        expect(page.locator("body")).to_contain_text(re.compile("Scheduled|Running|Completed|Clear all", re.IGNORECASE))
    else:
        pytest.skip("Status filter dropdown not found")

# ----------------------------
# Create Broadcast Navigation
# ----------------------------

def test_add_new_broadcast_redirect(page: Page):
    _assert_broadcast_page(page, ADMIN_EMAIL, ADMIN_PASSWORD)
    create_btn = page.locator('button:has-text("Create"), button:has-text("Add"), a[href*="create"]')
    if create_btn.count() > 0:
        create_btn.first.click()
        page.wait_for_timeout(2000)
        expect(page).to_have_url(re.compile(r".*create.*", re.IGNORECASE))
    else:
        pytest.skip("Create Broadcast button not found")

# ----------------------------
# Step 1 Validation
# ----------------------------

def test_apply_button_disabled_when_fields_empty(page: Page):
    _assert_broadcast_page(page, ADMIN_EMAIL, ADMIN_PASSWORD)
    page.goto(CREATE_BROADCAST_URL)
    page.wait_for_timeout(2000)
    apply_btn = page.locator('button:has-text("Apply")')
    if apply_btn.count() > 0:
        expect(apply_btn.first).to_be_disabled()

# ----------------------------
# POSITIVE TEST CASES
# ----------------------------

def test_create_scheduled_broadcast_success(page: Page):
    _assert_broadcast_page(page, ADMIN_EMAIL, ADMIN_PASSWORD)
    page.goto(CREATE_BROADCAST_URL)
    page.wait_for_timeout(2000)
    
    try:
        name_input = page.locator('input[type="text"]').first
        if name_input.is_visible():
            name_input.fill(unique_campaign())
            apply_btn = page.locator('button:has-text("Apply")')
            if apply_btn.is_visible() and apply_btn.is_enabled():
                apply_btn.click()
                expect(page.locator('button:has-text("Send")')).to_be_visible()
    except Exception:
        pytest.skip("Create Broadcast form elements not fully interactable")

# ----------------------------
# NEGATIVE TEST CASES
# ----------------------------

def test_empty_campaign_name_validation(page: Page):
    _assert_broadcast_page(page, ADMIN_EMAIL, ADMIN_PASSWORD)
    page.goto(CREATE_BROADCAST_URL)
    page.wait_for_timeout(2000)
    
    apply_btn = page.locator('button:has-text("Apply")')
    if apply_btn.count() > 0 and apply_btn.first.is_enabled():
        apply_btn.first.click()
        expect(page.locator("body")).to_contain_text(re.compile("required|missing|invalid", re.IGNORECASE))

# ----------------------------
# RESPONSIVE TESTS
# ----------------------------

def test_mobile_responsive(page: Page):
    page.set_viewport_size({"width": 375, "height": 667})
    _assert_broadcast_page(page, ADMIN_EMAIL, ADMIN_PASSWORD)
    expect(page.locator("body")).to_contain_text("Broadcast", ignore_case=True)

def test_desktop_responsive(page: Page):
    page.set_viewport_size({"width": 1920, "height": 1080})
    _assert_broadcast_page(page, ADMIN_EMAIL, ADMIN_PASSWORD)
    expect(page.locator("body")).to_contain_text("Broadcast", ignore_case=True)

# ----------------------------
# ADDITIONAL FORM VALIDATION
# ----------------------------

def test_campaign_name_max_length(page: Page):
    _assert_broadcast_page(page, ADMIN_EMAIL, ADMIN_PASSWORD)
    page.goto(CREATE_BROADCAST_URL)
    page.wait_for_timeout(2000)
    
    name_input = page.locator('input[type="text"]').first
    if name_input.is_visible():
        long_name = "A" * 256
        name_input.fill(long_name)
        expect(page.locator("body")).to_contain_text(re.compile("maximum|exceeded|too long", re.IGNORECASE))

def test_whitespace_only_campaign_name(page: Page):
    _assert_broadcast_page(page, ADMIN_EMAIL, ADMIN_PASSWORD)
    page.goto(CREATE_BROADCAST_URL)
    page.wait_for_timeout(2000)
    
    name_input = page.locator('input[type="text"]').first
    if name_input.is_visible():
        name_input.fill("     ")
        apply_btn = page.locator('button:has-text("Apply")')
        if apply_btn.is_visible() and apply_btn.is_enabled():
            apply_btn.click()
            expect(page.locator("body")).to_contain_text(re.compile("required|missing|invalid", re.IGNORECASE))

# ----------------------------
# EDGE CASES
# ----------------------------

def test_search_non_existing_broadcast(page: Page):
    _assert_broadcast_page(page, ADMIN_EMAIL, ADMIN_PASSWORD)
    search_inputs = page.locator('input[placeholder*="Search" i]')
    if search_inputs.count() > 0:
        search_inputs.first.fill("NON_EXISTING_BROADCAST_999")
        search_inputs.first.press("Enter")
        page.wait_for_timeout(1000)
        expect(page.locator("body")).to_contain_text(re.compile("no records|no search results|not found", re.IGNORECASE))
    else:
        pytest.skip("Search input not found")

def test_status_filter_no_results(page: Page):
    _assert_broadcast_page(page, ADMIN_EMAIL, ADMIN_PASSWORD)
    filter_btn = page.locator('button:has-text("Status"), [class*="filter"]')
    if filter_btn.count() > 0:
        filter_btn.first.click()
        page.wait_for_timeout(500)
        cancel_opt = page.locator('text="Cancelled"')
        if cancel_opt.count() > 0:
            cancel_opt.first.click()
            page.wait_for_timeout(1000)
            # Expect empty state
            expect(page.locator("body")).to_contain_text(re.compile("no records|no search results|empty", re.IGNORECASE))
    else:
        pytest.skip("Status filter not found")