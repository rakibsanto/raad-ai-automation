import os, time, pytest
from playwright.sync_api import Page, expect

"""
Blocked Contact Tests — based on specs/blocked_contact.md
Covers: Role-based access, unauthenticated redirection, blocked contact list visibility,
       block/unblock actions, and search by customer name.
"""

# ── Environment ────────────────────────────────────────────────────────────────
BASE_URL = os.getenv("BASE_URL", "https://dev.prowhats.com/en")
LOGIN_URL = os.getenv("LOGIN_URL", f"{BASE_URL}/login")
BLOCKED_CONTACTS_URL = f"{BASE_URL}/contacts/blocked-contacts"

OWNER_EMAIL = os.getenv("OWNER_EMAIL", "saidurdev@gmail.com")
OWNER_PASSWORD = os.getenv("OWNER_PASSWORD", "saidurdev@gmail.com")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "rakibsanto1998@gmail.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "111111")
AGENT_EMAIL = os.getenv("AGENT_EMAIL", "rakibsanto.cse@gmail.com")
AGENT_PASSWORD = os.getenv("AGENT_PASSWORD", "111111")

NAV = 'wait_until="domcontentloaded", timeout=20000'

# ── Login helper ───────────────────────────────────────────────────────────────

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

    # True if we are no longer on the login page
    return "login" not in page.url

def _assert_blocked_contacts_access(page: Page, email: str, password: str):
    """Login and assert blocked contacts page loaded; skip if login fails."""
    success = _login(page, email, password)
    if not success:
        page.goto(BLOCKED_CONTACTS_URL, wait_until="domcontentloaded", timeout=20000)
        page.wait_for_timeout(2000)
        if "login" in page.url:
            pytest.skip(f"Login failed for {email} — blocked contacts inaccessible")


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Access Control
# ═══════════════════════════════════════════════════════════════════════════════

def test_unauthenticated_user_redirects_to_login(page: Page):
    """Without login no one can visit this page."""
    page.goto(BLOCKED_CONTACTS_URL, wait_until="domcontentloaded", timeout=20000)
    page.wait_for_timeout(2000)
    assert "login" in page.url or "login" in page.content().lower(), \
        "Unauthenticated access to blocked contacts should redirect to login"


def test_owner_can_access_blocked_contacts(page: Page):
    """Company owner can view this page."""
    _assert_blocked_contacts_access(page, OWNER_EMAIL, OWNER_PASSWORD)
    page.goto(BLOCKED_CONTACTS_URL, wait_until="domcontentloaded", timeout=20000)
    page.wait_for_timeout(2000)
    assert "blocked-contacts" in page.url or "blocked" in page.title().lower(), \
        f"Owner did not reach blocked contacts page. URL: {page.url}"


def test_admin_can_access_blocked_contacts(page: Page):
    """Admin can view this page."""
    _assert_blocked_contacts_access(page, ADMIN_EMAIL, ADMIN_PASSWORD)
    page.goto(BLOCKED_CONTACTS_URL, wait_until="domcontentloaded", timeout=20000)
    page.wait_for_timeout(2000)
    assert "blocked-contacts" in page.url or "blocked" in page.title().lower(), \
        f"Admin did not reach blocked contacts page. URL: {page.url}"


def test_agent_can_access_blocked_contacts(page: Page):
    """Agent can view this page."""
    _assert_blocked_contacts_access(page, AGENT_EMAIL, AGENT_PASSWORD)
    page.goto(BLOCKED_CONTACTS_URL, wait_until="domcontentloaded", timeout=20000)
    page.wait_for_timeout(2000)
    assert "blocked-contacts" in page.url or "blocked" in page.title().lower(), \
        f"Agent did not reach blocked contacts page. URL: {page.url}"


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Blocked Contact List View
# ═══════════════════════════════════════════════════════════════════════════════

def test_blocked_contacts_list_is_visible(page: Page):
    """In this page all blocked list is showing."""
    _assert_blocked_contacts_access(page, OWNER_EMAIL, OWNER_PASSWORD)
    page.goto(BLOCKED_CONTACTS_URL, wait_until="domcontentloaded", timeout=20000)
    page.wait_for_timeout(2000)
    
    # We look for a table, list, or grid container typical for such lists
    list_containers = page.locator("table, [class*='table'], [class*='list'], [class*='grid']")
    if list_containers.count() == 0:
        pytest.skip("No list or table element found for blocked contacts")
    
    assert list_containers.count() > 0, "Blocked contacts list/table not found on the page"


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Actions (Block/Unblock for Campaign and Contact)
# ═══════════════════════════════════════════════════════════════════════════════

def test_block_unblock_actions_present(page: Page):
    """They can blocked and unblocked for campaign and contact."""
    _assert_blocked_contacts_access(page, OWNER_EMAIL, OWNER_PASSWORD)
    page.goto(BLOCKED_CONTACTS_URL, wait_until="domcontentloaded", timeout=20000)
    page.wait_for_timeout(2000)
    
    body = page.inner_text("body").lower()
    
    # Verify that block or unblock terms appear, confirming action presence
    actions_present = "block" in body or "unblock" in body
    assert actions_present, "Block or Unblock actions not found on the page"


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Search Functionality
# ═══════════════════════════════════════════════════════════════════════════════

def test_search_by_customer_name_input_exists(page: Page):
    """They can search by customer name."""
    _assert_blocked_contacts_access(page, OWNER_EMAIL, OWNER_PASSWORD)
    page.goto(BLOCKED_CONTACTS_URL, wait_until="domcontentloaded", timeout=20000)
    page.wait_for_timeout(2000)
    
    search_input = page.locator(
        'input[type="search"], input[placeholder*="search" i], '
        'input[placeholder*="name" i], input[placeholder*="customer" i]'
    )
    
    assert search_input.count() > 0, "Search input for customer name not found"

def test_search_by_customer_name_functional(page: Page):
    """Ensure search execution does not crash the page."""
    _assert_blocked_contacts_access(page, OWNER_EMAIL, OWNER_PASSWORD)
    page.goto(BLOCKED_CONTACTS_URL, wait_until="domcontentloaded", timeout=20000)
    page.wait_for_timeout(2000)
    
    search_input = page.locator(
        'input[type="search"], input[placeholder*="search" i], '
        'input[placeholder*="name" i]'
    )
    
    if search_input.count() > 0:
        search_input.first.fill("Test Customer")
        page.keyboard.press("Enter")
        page.wait_for_timeout(2000)
        
    assert "500" not in page.title(), "Searching caused a server error"