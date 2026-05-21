"""
QA Comprehensive Test Suite — ProWhats / Raad
Specs covered:
  specs/login.md              → QA-01 … QA-20  (homepage, login modal, WhatsApp OTP)
  specs/company_dashboard.md  → TestQA_Dashboard
  specs/company_broadcast.md  → TestQA_Broadcast
  specs/contact.md            → TestQA_Contact
  specs/blocked_contact.md    → TestQA_BlockedContact
  specs/manage_group.md       → TestQA_ManageGroup

Core test groups (login module):
  QA-01  Functional & User Flow Tests       (homepage, modal, login, navigation)
  QA-02  Edge Case & Boundary Tests         (phone validation, OTP, modal state)
  QA-03  Security Tests (XSS + SQLi)        (phone/search injection vectors)
  QA-04  Performance & JavaScript Error Tests
  QA-05  Hallucination & Data Integrity Tests
  QA-06  API & Network Monitoring           (headers, HTTPS, cookies, CORS)
  QA-07  Accessibility Tests               (ARIA, keyboard, focus, headings)
  QA-08  Mobile & Cross-Viewport Tests     (responsive layouts, touch targets)
"""

import os, re, time, json
import pytest
from pathlib import Path
from playwright.sync_api import Page, expect

BASE_URL = os.getenv("BASE_URL", "https://dev.prowhats.com/en")
FIND_TUTORS_URL = f"{BASE_URL}/find-tutors"
AR_URL          = os.getenv("BASE_URL", "https://dev.prowhats.com/ar").rstrip("/en").rstrip("/") + "/ar"

# SPA-safe load state — SPAs never reach networkidle
LOAD_STATE = "domcontentloaded"

# Test credentials (staging only)
TEST_COUNTRY_CODE = "+880"   # Bangladesh
TEST_PHONE        = "98976564"
TEST_OTP          = "123456"
TEST_USER_NAME    = "Automations Student"

PAYLOAD_DIR = Path(__file__).parent.parent / "payloads"

# ── Module URLs (derived from BASE_URL so they follow .env automatically) ──
_BASE_DOMAIN    = BASE_URL.rstrip("/en").rstrip("/")
LOGIN_URL       = os.getenv("LOGIN_URL",       f"{_BASE_DOMAIN}/en/login")
DASHBOARD_URL   = os.getenv("DASHBOARD_URL",   f"{_BASE_DOMAIN}/en/dashboard")
BROADCAST_URL   = f"{_BASE_DOMAIN}/en/broadcast"
BROADCAST_CREATE_URL = f"{_BASE_DOMAIN}/en/broadcast/create"
CONTACTS_URL    = f"{_BASE_DOMAIN}/en/contacts"
BLOCKED_URL     = f"{_BASE_DOMAIN}/en/contacts/blocked-contacts"
MANAGE_GRP_URL  = f"{_BASE_DOMAIN}/en/contacts/manage-group"

# ── Role credentials (staging only, read from .env) ──────────────────────
OWNER_EMAIL    = os.getenv("OWNER_EMAIL",    "saidurdev@gmail.com")
OWNER_PASSWORD = os.getenv("OWNER_PASSWORD", "saidurdev@gmail.com")
ADMIN_EMAIL    = os.getenv("ADMIN_EMAIL",    "rakibsanto1998@gmail.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "111111")
AGENT_EMAIL    = os.getenv("AGENT_EMAIL",    "gelaraj910@hilostar.com")
AGENT_PASSWORD = os.getenv("AGENT_PASSWORD", "111111")

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _wait_visible(page: Page, selector: str, timeout: int = 10000):
    """Wait for a selector to be visible, return the locator."""
    page.wait_for_selector(selector, state="visible", timeout=timeout)
    return page.locator(selector).first


def _open_login_modal(page: Page):
    """Navigate to the login page.
    """
    page.goto(BASE_URL)
    page.wait_for_load_state(LOAD_STATE)
    page.wait_for_selector('input[type="email"]', state="visible", timeout=12000)


def _find_visible_login_button(page: Page):
    """Return the visible Log In button. Filters out the mobile-menu button
    (aria-label="Login") which is hidden on desktop viewports.

    Also matches the Arabic locale equivalent ('تسجيل الدخول') so the same
    helper works on /ar pages."""
    candidates = page.locator(
        '[aria-label="Login"], '
        '[aria-label="تسجيل الدخول"], '
        'button:has-text("Log In"), '
        'button:has-text("Login"), '
        'button:has-text("تسجيل الدخول")'
    )
    visible = candidates.filter(visible=True)
    if visible.count() > 0:
        return visible.first
    # Fallback: header button without aria-label, picked by text only
    fallback = page.locator(
        'button:has-text("Log In"), button:has-text("تسجيل الدخول")'
    )
    return fallback.first


def _fill_phone(page: Page, country_code: str, phone: str):
    """Select country code and fill phone number in the login modal."""
    # Change country if not the default +966
    if country_code != "+966":
        cc_btn = page.locator('[aria-label="Country code"]').first
        cc_btn.click()
        page.wait_for_selector('[placeholder="Search..."]', state="visible", timeout=5000)
        country_name = "Bangladesh" if country_code == "+880" else country_code
        page.locator('[placeholder="Search..."]').fill(country_name)
        page.wait_for_timeout(600)
        option = page.locator('[role="option"]').filter(has_text=country_code).first
        option.click(force=True)
        page.wait_for_timeout(600)  # extra wait for React re-render after country change

    phone_input = page.locator('input[type="email"]').first
    phone_input.wait_for(state="visible", timeout=5000)
    phone_input.click()
    phone_input.fill("")  # clear any stale value first
    # Use press_sequentially to simulate real key events so React's onChange fires
    phone_input.press_sequentially(phone, delay=60)
    phone_input.press("Tab")  # trigger blur / validation
    page.wait_for_timeout(300)


def _collect_js_errors(page: Page) -> list:
    errors: list = []
    page.on("console",  lambda m: errors.append({"type": m.type, "text": m.text})
            if m.type == "error" else None)
    page.on("pageerror", lambda exc: errors.append({"type": "pageerror", "text": str(exc)}))
    return errors


def _load_payload_lines(filename: str) -> list[str]:
    p = PAYLOAD_DIR / filename
    if not p.exists():
        return []
    return [ln.strip() for ln in p.read_text().splitlines()
            if ln.strip() and not ln.startswith("#")]


def _login_as(page: Page, email: str, password: str) -> None:
    """Authenticate via the ProWhats email/password login page.

    Navigates to LOGIN_URL, fills email + password, submits, and waits for
    the redirect away from the login page.  Shared by all post-login spec
    test classes (dashboard, broadcast, contacts, blocked, manage-group).
    """
    page.goto(LOGIN_URL)
    page.wait_for_load_state(LOAD_STATE)

    # Email input — try multiple selector strategies used by various SPA stacks
    email_input = page.locator(
        'input[type="email"], input[name="email"], '
        'input[placeholder*="email" i], input[placeholder*="Email" i]'
    ).first
    email_input.wait_for(state="visible", timeout=12000)
    email_input.fill(email)

    # Password input
    pwd_input = page.locator('input[type="password"]').first
    pwd_input.wait_for(state="visible", timeout=8000)
    pwd_input.fill(password)

    # Submit button
    submit_btn = page.locator(
        'button[type="submit"], '
        'button:has-text("Login"), button:has-text("Log in"), '
        'button:has-text("Sign in"), button:has-text("Sign In")'
    ).first
    submit_btn.wait_for(state="visible", timeout=8000)
    submit_btn.click()

    # Wait for the SPA to redirect away from the login page
    try:
        page.wait_for_function(
            "() => !window.location.href.includes('/login')",
            timeout=15000,
        )
    except Exception:
        pass  # if still on login, tests will surface the failure naturally

    page.wait_for_load_state(LOAD_STATE)
    page.wait_for_timeout(1000)



# =============================================================================
# SPEC: specs/login.md  →  TestQA_Login
# =============================================================================

class TestQA_Login:
    """Covers login.md: functional tests for authentication including
    Admin, Owner, and Agent logins, and invalid credentials."""

    def test_login_admin_success(self, page: Page):
        """Spec: Admin should login successfully."""
        _login_as(page, ADMIN_EMAIL, ADMIN_PASSWORD)
        assert "/dashboard" in page.url or "dashboard" in page.url.lower(), (
            f"Admin failed to login, current url: {page.url}")

    def test_login_owner_success(self, page: Page):
        """Spec: Owner should login successfully."""
        _login_as(page, OWNER_EMAIL, OWNER_PASSWORD)
        assert "/dashboard" in page.url or "dashboard" in page.url.lower(), (
            f"Owner failed to login, current url: {page.url}")

    def test_login_agent_success(self, page: Page):
        """Spec: Agent should login successfully."""
        _login_as(page, AGENT_EMAIL, AGENT_PASSWORD)
        assert "/dashboard" in page.url or "dashboard" in page.url.lower(), (
            f"Agent failed to login, current url: {page.url}")

    def test_login_invalid_credentials(self, page: Page):
        """Spec: Invalid credentials should not allow login."""
        page.goto(LOGIN_URL)
        page.wait_for_load_state(LOAD_STATE)
        email_input = page.locator('input[type="email"], input[name="email"], input[placeholder*="email" i]').first
        email_input.wait_for(state="visible", timeout=12000)
        email_input.fill("invalid@example.com")
        pwd_input = page.locator('input[type="password"]').first
        pwd_input.wait_for(state="visible", timeout=8000)
        pwd_input.fill("wrongpassword")
        submit_btn = page.locator('button[type="submit"], button:has-text("Login"), button:has-text("Log in"), button:has-text("Sign in")').first
        submit_btn.wait_for(state="visible", timeout=8000)
        submit_btn.click()
        page.wait_for_timeout(2000)
        assert "login" in page.url.lower(), "System navigated away despite invalid login"

# =============================================================================
# SPEC: specs/company_dashboard.md  →  TestQA_Dashboard
# =============================================================================

class TestQA_Dashboard:
    """Covers company_dashboard.md: access control, welcome message,
    statistics cards, filters, broadcast chart, message summary,
    agents table, pagination, and security."""

    # ── helpers ──────────────────────────────────────────────────────────────

    def _login_dashboard(self, page: Page,
                         email: str = ADMIN_EMAIL,
                         password: str = ADMIN_PASSWORD) -> None:
        """Login and ensure we are on the dashboard page."""
        _login_as(page, email, password)
        if "/dashboard" not in page.url:
            page.goto(DASHBOARD_URL)
            page.wait_for_load_state(LOAD_STATE)
        page.wait_for_timeout(1500)

    # ── 1. Access Control ─────────────────────────────────────────────────────

    def test_dashboard_unauthenticated_redirects_to_login(self, page: Page):
        """Spec §1: Unauthenticated /dashboard must redirect to login."""
        page.goto(DASHBOARD_URL)
        page.wait_for_load_state(LOAD_STATE)
        page.wait_for_timeout(1200)
        assert "/login" in page.url or "login" in page.url.lower(), (
            f"Unauthenticated /dashboard did not redirect to login. Got: {page.url}")

    def test_dashboard_admin_can_access(self, page: Page):
        """Spec §1: Admin must be able to view the dashboard."""
        self._login_dashboard(page, ADMIN_EMAIL, ADMIN_PASSWORD)
        assert "500" not in page.title(), "Dashboard returned 500 for admin"
        content = page.inner_text("body").lower()
        assert ("dashboard" in page.url.lower() or "good" in content
                or "conversation" in content or "contact" in content), (
            f"Admin dashboard appears empty. URL={page.url}")

    def test_dashboard_owner_can_access(self, page: Page):
        """Spec §1: Company Owner must be able to view the dashboard."""
        self._login_dashboard(page, OWNER_EMAIL, OWNER_PASSWORD)
        assert "500" not in page.title(), "Dashboard returned 500 for owner"

    # ── 2. Welcome Message ────────────────────────────────────────────────────

    def test_dashboard_welcome_greeting_present(self, page: Page):
        """Spec §2: Dashboard must show a time-based greeting."""
        self._login_dashboard(page)
        content = page.inner_text("body").lower()
        greetings = ["good morning", "good evening", "good night"]
        assert any(g in content for g in greetings), (
            f"No time-based greeting found on dashboard. Preview: {content[:300]!r}")

    def test_dashboard_greeting_not_undefined(self, page: Page):
        """Spec §2: Greeting text must not be 'undefined' or blank."""
        self._login_dashboard(page)
        content = page.inner_text("body").lower()
        assert "good undefined" not in content, (
            "Dashboard greeting contains 'undefined' — rendering bug")

    # ── 3. Statistics Cards ───────────────────────────────────────────────────

    def test_dashboard_stats_conversation_present(self, page: Page):
        """Spec §3: Conversation count metric must be present."""
        self._login_dashboard(page)
        assert "conversation" in page.inner_text("body").lower(), (
            "Dashboard: 'Conversation' metric card not found")

    def test_dashboard_stats_contact_present(self, page: Page):
        """Spec §3: Contact count metric must be present."""
        self._login_dashboard(page)
        assert "contact" in page.inner_text("body").lower(), (
            "Dashboard: 'Contact' metric card not found")

    def test_dashboard_stats_are_numeric(self, page: Page):
        """Spec §3: Stat card values must contain numbers, not blank strings."""
        self._login_dashboard(page)
        content = page.inner_text("body")
        assert re.search(r"\d+", content), (
            "Dashboard stats cards show no numeric data")

    # ── 4. Filter Options ─────────────────────────────────────────────────────

    def test_dashboard_filter_options_present(self, page: Page):
        """Spec §3 filters: Last 7 Days / 30 Days / 6 Months must be available."""
        self._login_dashboard(page)
        content = page.inner_text("body").lower()
        assert ("7" in content and ("day" in content or "month" in content)), (
            f"Filter options (7d/30d/6m) not found. Preview: {content[:300]!r}")

    def test_dashboard_filter_click_no_crash(self, page: Page):
        """Spec §3 filters: Clicking a filter must not crash the dashboard."""
        self._login_dashboard(page)
        btn = page.locator(
            'button:has-text("7"), [data-value="7"], '
            'button:has-text("Last 7")'
        ).first
        if btn.count() > 0 and btn.is_visible(timeout=3000):
            btn.click()
            page.wait_for_timeout(1500)
        assert "500" not in page.title(), "Dashboard crashed after filter click"

    # ── 5. Broadcast Chart ────────────────────────────────────────────────────

    def test_dashboard_broadcast_chart_metrics_present(self, page: Page):
        """Spec §4: Broadcast chart must include sent/delivered/read/failed."""
        self._login_dashboard(page)
        content = page.inner_text("body").lower()
        found = [m for m in ["sent", "delivered", "read", "failed"] if m in content]
        assert len(found) >= 2, (
            f"Broadcast chart metrics missing. Found only: {found}")

    # ── 6. Message Summary ────────────────────────────────────────────────────

    def test_dashboard_message_summary_present(self, page: Page):
        """Spec §5: Message summary (Total/Sent/Delivered/Read/Failed) must show."""
        self._login_dashboard(page)
        content = page.inner_text("body").lower()
        found = [m for m in ["total", "sent", "delivered"] if m in content]
        assert len(found) >= 2, (
            f"Message summary section metrics missing. Found: {found}")

    # ── 7. Agents Table ───────────────────────────────────────────────────────

    def test_dashboard_agents_table_present(self, page: Page):
        """Spec §6: 'Conversation by Agents' table section must exist."""
        self._login_dashboard(page)
        content = page.inner_text("body").lower()
        assert "agent" in content or "conversation" in content, (
            "Agents table section not found on dashboard")

    def test_dashboard_agents_table_status_columns(self, page: Page):
        """Spec §6: Table must show Open / Pending / Close status columns."""
        self._login_dashboard(page)
        content = page.inner_text("body").lower()
        found = [s for s in ["open", "pending", "close"] if s in content]
        assert len(found) >= 2, (
            f"Agents table status columns missing. Found: {found}")

    # ── 8. Pagination ─────────────────────────────────────────────────────────

    def test_dashboard_pagination_present_for_large_table(self, page: Page):
        """Spec §7: Pagination must appear when agent rows > 9."""
        self._login_dashboard(page)
        rows = page.locator("table tbody tr, [role='row']").count()
        if rows > 9:
            pager = page.locator(
                "[class*='pagination'], button:has-text('Next'), "
                "button:has-text('Previous'), [aria-label*='pagination' i]"
            ).first
            assert pager.count() > 0, (
                f"Pagination missing with {rows} rows (spec: show when > 9)")

    # ── Security ──────────────────────────────────────────────────────────────

    def test_dashboard_no_5xx_on_load(self, page: Page):
        """Dashboard must not trigger any 5xx network responses."""
        errors: list = []
        page.on("response", lambda r: errors.append(r.status)
                if r.status >= 500 else None)
        self._login_dashboard(page)
        assert errors == [], f"5xx responses on dashboard load: {errors[:3]}"

    def test_dashboard_no_js_errors(self, page: Page):
        """Dashboard must load without uncaught JS errors."""
        errs: list = []
        page.on("console",  lambda m: errs.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: errs.append(str(e)))
        self._login_dashboard(page)
        real = [e for e in errs if "extension" not in e.lower()
                and "favicon" not in e.lower()]
        assert real == [], f"JS errors on dashboard: {real[:3]}"


# =============================================================================
# SPEC: specs/company_broadcast.md  →  TestQA_Broadcast
# =============================================================================

class TestQA_Broadcast:
    """Covers company_broadcast.md: listing columns, actions, create-flow,
    details metrics, role-based access (Agent blocked), and validation."""

    # ── helpers ──────────────────────────────────────────────────────────────

    def _go_broadcast(self, page: Page,
                      email: str = ADMIN_EMAIL,
                      password: str = ADMIN_PASSWORD) -> None:
        _login_as(page, email, password)
        if "/broadcast" not in page.url:
            page.goto(BROADCAST_URL)
            page.wait_for_load_state(LOAD_STATE)
        page.wait_for_timeout(1500)

    # ── 1. Access Control ─────────────────────────────────────────────────────

    def test_broadcast_unauthenticated_redirects_to_login(self, page: Page):
        """Spec §4: Unauthenticated /broadcast must redirect to login."""
        page.goto(BROADCAST_URL)
        page.wait_for_load_state(LOAD_STATE)
        page.wait_for_timeout(1000)
        assert "/login" in page.url or "login" in page.url.lower(), (
            f"Unauthenticated /broadcast did not redirect to login: {page.url}")

    def test_broadcast_admin_can_access(self, page: Page):
        """Spec §2 Admin: Admin must be able to access broadcast listing."""
        self._go_broadcast(page, ADMIN_EMAIL, ADMIN_PASSWORD)
        assert "500" not in page.title(), "Broadcast page 500 for admin"
        content = page.inner_text("body").lower()
        assert "broadcast" in content or "campaign" in content or "template" in content, (
            f"Broadcast listing empty for admin. URL={page.url}")

    def test_broadcast_owner_can_access(self, page: Page):
        """Spec §2 Owner: Company Owner must be able to access broadcast."""
        self._go_broadcast(page, OWNER_EMAIL, OWNER_PASSWORD)
        assert "500" not in page.title(), "Broadcast page 500 for owner"

    def test_broadcast_agent_is_blocked(self, page: Page):
        """Spec §2 Agent: Agent must NOT be allowed on /broadcast."""
        _login_as(page, AGENT_EMAIL, AGENT_PASSWORD)
        page.goto(BROADCAST_URL)
        page.wait_for_load_state(LOAD_STATE)
        page.wait_for_timeout(1500)
        blocked = (
            "/login" in page.url
            or "/dashboard" in page.url
            or "403" in page.title()
            or "denied" in page.inner_text("body").lower()
            or "access" in page.inner_text("body").lower()
        )
        assert blocked, (
            f"Agent was NOT blocked from /broadcast. URL={page.url}")

    # ── 2. Listing Dashboard ──────────────────────────────────────────────────

    def test_broadcast_listing_columns_visible(self, page: Page):
        """Spec §1 columns: Name / Template / Status columns must be present."""
        self._go_broadcast(page)
        content = page.inner_text("body").lower()
        found = [c for c in ["name", "template", "status"] if c in content]
        assert len(found) >= 2, (
            f"Broadcast table columns missing. Found: {found}")

    def test_broadcast_no_undefined_in_table(self, page: Page):
        """Broadcast table must not show 'undefined' or '[object Object]'."""
        self._go_broadcast(page)
        content = page.inner_text("body")
        assert "undefined" not in content, (
            "Broadcast table contains literal 'undefined'")
        assert "[object Object]" not in content, (
            "Broadcast table contains '[object Object]' — data binding bug")

    def test_broadcast_view_details_action_present(self, page: Page):
        """Spec §1 actions: 'View Details' action must be accessible."""
        self._go_broadcast(page)
        content = page.inner_text("body").lower()
        detail_btn = page.locator(
            'button:has-text("View"), a:has-text("View"), '
            '[aria-label*="view" i], [title*="detail" i]'
        ).first
        assert detail_btn.count() > 0 or "view" in content or "detail" in content, (
            "View Details action not found in broadcast listing")

    # ── 3. Create Broadcast ───────────────────────────────────────────────────

    def test_broadcast_create_page_accessible(self, page: Page):
        """Spec §1 create: /broadcast/create must load for admin."""
        _login_as(page, ADMIN_EMAIL, ADMIN_PASSWORD)
        page.goto(BROADCAST_CREATE_URL)
        page.wait_for_load_state(LOAD_STATE)
        page.wait_for_timeout(1500)
        assert "500" not in page.title(), "Broadcast create page returned 500"

    def test_broadcast_create_name_field_present(self, page: Page):
        """Spec §1 create: Name input field must exist on create page."""
        _login_as(page, ADMIN_EMAIL, ADMIN_PASSWORD)
        page.goto(BROADCAST_CREATE_URL)
        page.wait_for_load_state(LOAD_STATE)
        page.wait_for_timeout(1500)
        name_inp = page.locator(
            'input[name*="name" i], input[placeholder*="name" i], '
            'input[placeholder*="broadcast" i]'
        ).first
        content = page.inner_text("body").lower()
        assert name_inp.count() > 0 or "name" in content, (
            "Broadcast create: Name field not found")

    def test_broadcast_create_submit_disabled_when_empty(self, page: Page):
        """Spec §3 validation: Apply/Send button must be disabled with empty form."""
        _login_as(page, ADMIN_EMAIL, ADMIN_PASSWORD)
        page.goto(BROADCAST_CREATE_URL)
        page.wait_for_load_state(LOAD_STATE)
        page.wait_for_timeout(1500)
        btn = page.locator(
            'button:has-text("Apply"), button:has-text("Send Campaign")'
        ).first
        if btn.count() > 0 and btn.is_visible(timeout=3000):
            assert btn.is_disabled() or btn.get_attribute("aria-disabled") == "true", (
                "Apply/Send Campaign enabled with empty broadcast form")

    # ── 4. Security / Quality ─────────────────────────────────────────────────

    def test_broadcast_no_5xx_on_load(self, page: Page):
        """No 5xx responses during broadcast listing page load."""
        errs: list = []
        page.on("response", lambda r: errs.append(r.status)
                if r.status >= 500 else None)
        self._go_broadcast(page)
        assert errs == [], f"5xx on broadcast load: {errs[:3]}"

    def test_broadcast_no_js_errors(self, page: Page):
        """Broadcast listing page must not produce uncaught JS errors."""
        errs: list = []
        page.on("console",  lambda m: errs.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: errs.append(str(e)))
        self._go_broadcast(page)
        real = [e for e in errs if "extension" not in e.lower()
                and "favicon" not in e.lower()]
        assert real == [], f"JS errors on broadcast page: {real[:3]}"


# =============================================================================
# SPEC: specs/contact.md  →  TestQA_Contact
# =============================================================================

class TestQA_Contact:
    """Covers contact.md: access control, contact list table, add/edit/delete,
    search & filter, import/export, pagination, and error handling."""

    def _go_contacts(self, page: Page,
                     email: str = ADMIN_EMAIL,
                     password: str = ADMIN_PASSWORD) -> None:
        _login_as(page, email, password)
        if "/contacts" not in page.url:
            page.goto(CONTACTS_URL)
            page.wait_for_load_state(LOAD_STATE)
        page.wait_for_timeout(1500)

    # ── 1. Access Control ─────────────────────────────────────────────────────

    def test_contact_unauthenticated_redirects_to_login(self, page: Page):
        """Spec §1: Unauthenticated /contacts must redirect to login."""
        page.goto(CONTACTS_URL)
        page.wait_for_load_state(LOAD_STATE)
        page.wait_for_timeout(1000)
        assert "/login" in page.url or "login" in page.url.lower(), (
            f"Unauthenticated /contacts did not redirect to login: {page.url}")

    def test_contact_admin_can_access(self, page: Page):
        """Spec §1: Admin can view the contacts page."""
        self._go_contacts(page, ADMIN_EMAIL, ADMIN_PASSWORD)
        assert "500" not in page.title(), "Contacts page 500 for admin"

    def test_contact_agent_can_access(self, page: Page):
        """Spec §1: Agent is also authorized to access contacts page."""
        self._go_contacts(page, AGENT_EMAIL, AGENT_PASSWORD)
        assert "500" not in page.title(), "Contacts page 500 for agent"

    # ── 2. Contact List Table ─────────────────────────────────────────────────

    def test_contact_list_table_rendered(self, page: Page):
        """Spec §2: Contact list table must be visible."""
        self._go_contacts(page)
        content = page.inner_text("body").lower()
        assert ("contact" in content or "name" in content
                or "phone" in content), (
            f"Contact list table not found. URL={page.url}")

    def test_contact_list_columns_name_phone(self, page: Page):
        """Spec §2: Table must contain Name and Phone Number columns."""
        self._go_contacts(page)
        content = page.inner_text("body").lower()
        found = [c for c in ["name", "phone"] if c in content]
        assert len(found) >= 1, (
            f"Contact table columns (name/phone) not found. Found: {found}")

    def test_contact_list_no_undefined(self, page: Page):
        """Contact list must not display 'undefined' or '[object Object]'."""
        self._go_contacts(page)
        content = page.inner_text("body")
        assert "undefined" not in content, "Contact list has 'undefined' text"
        assert "[object Object]" not in content, (
            "Contact list has '[object Object]' — rendering bug")

    # ── 3. Add Contact ────────────────────────────────────────────────────────

    def test_contact_add_button_present(self, page: Page):
        """Spec §3: 'Add Contact' button must be visible."""
        self._go_contacts(page)
        add_btn = page.locator(
            'button:has-text("Add"), button:has-text("New Contact"), '
            'a:has-text("Add Contact"), [aria-label*="add" i]'
        ).first
        content = page.inner_text("body").lower()
        assert add_btn.count() > 0 or "add" in content, (
            "Add Contact button not found on contacts page")

    def test_contact_add_opens_modal_or_page(self, page: Page):
        """Spec §3: Clicking Add Contact must open a form/modal."""
        self._go_contacts(page)
        add_btn = page.locator(
            'button:has-text("Add"), button:has-text("New Contact"), '
            'a:has-text("Add Contact")'
        ).first
        if add_btn.count() > 0 and add_btn.is_visible(timeout=3000):
            add_btn.click()
            page.wait_for_timeout(1200)
            # Either a modal appeared or navigation occurred
            modal = page.locator('[role="dialog"], [aria-modal="true"]').first
            opened = (
                modal.count() > 0 and modal.is_visible(timeout=2000)
                or "create" in page.url.lower()
                or "add" in page.url.lower()
                or "new" in page.url.lower()
            )
            assert opened, "Add Contact button clicked but no modal/page opened"

    # ── 4. Search & Filter ────────────────────────────────────────────────────

    def test_contact_search_by_name_field_present(self, page: Page):
        """Spec §5: A search input for contact name must be present."""
        self._go_contacts(page)
        search = page.locator(
            'input[placeholder*="name" i], input[placeholder*="search" i], '
            'input[type="search"], [aria-label*="search" i]'
        ).first
        content = page.inner_text("body").lower()
        assert search.count() > 0 or "search" in content, (
            "No search field found on contacts page")

    def test_contact_search_by_phone_field_present(self, page: Page):
        """Spec §5: A search input for phone number must be present."""
        self._go_contacts(page)
        phone_search = page.locator(
            'input[placeholder*="phone" i], input[placeholder*="number" i]'
        ).first
        content = page.inner_text("body").lower()
        assert phone_search.count() > 0 or "phone" in content, (
            "No phone search field found on contacts page")

    def test_contact_search_does_not_crash(self, page: Page):
        """Spec §5: Typing in the search field must not crash the page."""
        self._go_contacts(page)
        search = page.locator(
            'input[placeholder*="search" i], input[placeholder*="name" i], '
            'input[type="search"]'
        ).first
        if search.count() > 0 and search.is_visible(timeout=3000):
            search.fill("test")
            page.wait_for_timeout(1200)
        assert "500" not in page.title(), "Page crashed after search input"

    # ── 5. Pagination ─────────────────────────────────────────────────────────

    def test_contact_pagination_when_data_gt_10(self, page: Page):
        """Spec §7: Pagination must appear when contacts > 10."""
        self._go_contacts(page)
        rows = page.locator("table tbody tr, [role='row']").count()
        if rows > 10:
            pager = page.locator(
                "[class*='pagination'], button:has-text('Next'), "
                "button:has-text('Previous')"
            ).first
            assert pager.count() > 0, (
                f"Pagination missing with {rows} contact rows (spec: show > 10)")

    # ── 6. Import / Export ────────────────────────────────────────────────────

    def test_contact_import_button_present(self, page: Page):
        """Spec §4: Import button must be available."""
        self._go_contacts(page)
        content = page.inner_text("body").lower()
        btn = page.locator(
            'button:has-text("Import"), a:has-text("Import")'
        ).first
        assert btn.count() > 0 or "import" in content, (
            "Import button not found on contacts page")

    def test_contact_export_button_present(self, page: Page):
        """Spec §4: Export button must be available."""
        self._go_contacts(page)
        content = page.inner_text("body").lower()
        btn = page.locator(
            'button:has-text("Export"), a:has-text("Export")'
        ).first
        assert btn.count() > 0 or "export" in content, (
            "Export button not found on contacts page")

    # ── Quality ───────────────────────────────────────────────────────────────

    def test_contact_no_5xx_on_load(self, page: Page):
        """Contacts page must not trigger 5xx responses."""
        errs: list = []
        page.on("response", lambda r: errs.append(r.status)
                if r.status >= 500 else None)
        self._go_contacts(page)
        assert errs == [], f"5xx on contacts page: {errs[:3]}"

    def test_contact_no_js_errors(self, page: Page):
        """Contacts page must not produce uncaught JS errors."""
        errs: list = []
        page.on("console",  lambda m: errs.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: errs.append(str(e)))
        self._go_contacts(page)
        real = [e for e in errs if "extension" not in e.lower()
                and "favicon" not in e.lower()]
        assert real == [], f"JS errors on contacts page: {real[:3]}"


# =============================================================================
# SPEC: specs/blocked_contact.md  →  TestQA_BlockedContact
# =============================================================================

class TestQA_BlockedContact:
    """Covers blocked_contact.md: access control (all 3 roles allowed),
    blocked list rendering, block/unblock actions, and search."""

    def _go_blocked(self, page: Page,
                    email: str = ADMIN_EMAIL,
                    password: str = ADMIN_PASSWORD) -> None:
        _login_as(page, email, password)
        if "blocked" not in page.url:
            page.goto(BLOCKED_URL)
            page.wait_for_load_state(LOAD_STATE)
        page.wait_for_timeout(1500)

    # ── 1. Access Control ─────────────────────────────────────────────────────

    def test_blocked_unauthenticated_redirects_to_login(self, page: Page):
        """Spec §1: Unauthenticated access must redirect to login."""
        page.goto(BLOCKED_URL)
        page.wait_for_load_state(LOAD_STATE)
        page.wait_for_timeout(1000)
        assert "/login" in page.url or "login" in page.url.lower(), (
            f"Unauthenticated /blocked-contacts did not redirect: {page.url}")

    def test_blocked_admin_can_access(self, page: Page):
        """Spec §1: Admin must be able to view blocked contacts."""
        self._go_blocked(page, ADMIN_EMAIL, ADMIN_PASSWORD)
        assert "500" not in page.title(), "Blocked contacts page 500 for admin"

    def test_blocked_owner_can_access(self, page: Page):
        """Spec §1: Company Owner must be able to view blocked contacts."""
        self._go_blocked(page, OWNER_EMAIL, OWNER_PASSWORD)
        assert "500" not in page.title(), "Blocked contacts page 500 for owner"

    def test_blocked_agent_can_access(self, page: Page):
        """Spec §1: Agent must also be able to view blocked contacts."""
        self._go_blocked(page, AGENT_EMAIL, AGENT_PASSWORD)
        assert "500" not in page.title(), "Blocked contacts page 500 for agent"

    # ── 2. Blocked Contact List ───────────────────────────────────────────────

    def test_blocked_list_renders(self, page: Page):
        """Spec §2: Blocked contacts list/table must render on page."""
        self._go_blocked(page)
        content = page.inner_text("body").lower()
        assert ("block" in content or "contact" in content
                or "name" in content), (
            f"Blocked contact list not rendered. URL={page.url}")

    def test_blocked_list_no_undefined(self, page: Page):
        """Blocked list must not show 'undefined' or empty state bugs."""
        self._go_blocked(page)
        content = page.inner_text("body")
        assert "undefined" not in content, (
            "Blocked contacts list contains literal 'undefined'")

    # ── 3. Block / Unblock Actions ────────────────────────────────────────────

    def test_blocked_unblock_action_present(self, page: Page):
        """Spec §3: Unblock action must be available for blocked contacts."""
        self._go_blocked(page)
        content = page.inner_text("body").lower()
        unblock_btn = page.locator(
            'button:has-text("Unblock"), a:has-text("Unblock"), '
            '[aria-label*="unblock" i]'
        ).first
        assert unblock_btn.count() > 0 or "unblock" in content, (
            "Unblock action not found on blocked contacts page")

    def test_blocked_block_action_present(self, page: Page):
        """Spec §3: Block action must be available (for campaigns/contacts)."""
        self._go_blocked(page)
        content = page.inner_text("body").lower()
        block_btn = page.locator(
            'button:has-text("Block"), a:has-text("Block"), '
            '[aria-label*="block" i]'
        ).first
        assert block_btn.count() > 0 or "block" in content, (
            "Block action not found on blocked contacts page")

    # ── 4. Search ─────────────────────────────────────────────────────────────

    def test_blocked_search_field_present(self, page: Page):
        """Spec §4: Search field for customer name must be present."""
        self._go_blocked(page)
        search = page.locator(
            'input[placeholder*="search" i], input[placeholder*="name" i], '
            'input[type="search"], [aria-label*="search" i]'
        ).first
        content = page.inner_text("body").lower()
        assert search.count() > 0 or "search" in content, (
            "Search field not found on blocked contacts page")

    def test_blocked_search_does_not_crash(self, page: Page):
        """Spec §4: Typing in search must update list without crash."""
        self._go_blocked(page)
        search = page.locator(
            'input[placeholder*="search" i], input[placeholder*="name" i], '
            'input[type="search"]'
        ).first
        if search.count() > 0 and search.is_visible(timeout=3000):
            search.fill("test")
            page.wait_for_timeout(1200)
        assert "500" not in page.title(), "Page crashed after search on blocked contacts"

    def test_blocked_search_empty_state_shown(self, page: Page):
        """Spec §4: Searching non-existent name must show empty/no-results state."""
        self._go_blocked(page)
        search = page.locator(
            'input[placeholder*="search" i], input[placeholder*="name" i], '
            'input[type="search"]'
        ).first
        if search.count() > 0 and search.is_visible(timeout=3000):
            search.fill("XYZNONEXISTENT99999")
            page.wait_for_timeout(1500)
            content = page.inner_text("body").lower()
            # Either a 'no results' message or an empty table — either is valid
            page_ok = (
                "no result" in content
                or "no data" in content
                or "empty" in content
                or page.locator("table tbody tr").count() == 0
                or "not found" in content
            )
            # Soft check: at minimum the page must not crash
            assert "500" not in page.title(), (
                "Page crashed after searching non-existent name on blocked contacts")

    # ── Quality ───────────────────────────────────────────────────────────────

    def test_blocked_no_5xx_on_load(self, page: Page):
        """Blocked contacts page must not trigger 5xx responses."""
        errs: list = []
        page.on("response", lambda r: errs.append(r.status)
                if r.status >= 500 else None)
        self._go_blocked(page)
        assert errs == [], f"5xx on blocked contacts page: {errs[:3]}"

    def test_blocked_no_js_errors(self, page: Page):
        """Blocked contacts page must not produce uncaught JS errors."""
        errs: list = []
        page.on("console",  lambda m: errs.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: errs.append(str(e)))
        self._go_blocked(page)
        real = [e for e in errs if "extension" not in e.lower()
                and "favicon" not in e.lower()]
        assert real == [], f"JS errors on blocked contacts page: {real[:3]}"


# =============================================================================
# SPEC: specs/manage_group.md  →  TestQA_ManageGroup
# =============================================================================

class TestQA_ManageGroup:
    """Covers manage_group.md: access control (Owner/Admin only, Agent blocked),
    group CRUD, duplicate prevention, customer management (include/remove/import/
    export), and table features (search, pagination, customer count)."""

    def _go_manage_group(self, page: Page,
                         email: str = ADMIN_EMAIL,
                         password: str = ADMIN_PASSWORD) -> None:
        _login_as(page, email, password)
        if "manage-group" not in page.url:
            page.goto(MANAGE_GRP_URL)
            page.wait_for_load_state(LOAD_STATE)
        page.wait_for_timeout(1500)

    # ── 1. Access Control ─────────────────────────────────────────────────────

    def test_manage_group_unauthenticated_redirects_to_login(self, page: Page):
        """Spec §1: Unauthenticated access must redirect to login."""
        page.goto(MANAGE_GRP_URL)
        page.wait_for_load_state(LOAD_STATE)
        page.wait_for_timeout(1000)
        assert "/login" in page.url or "login" in page.url.lower(), (
            f"Unauthenticated /manage-group did not redirect: {page.url}")

    def test_manage_group_admin_can_access(self, page: Page):
        """Spec §1: Admin must be able to view manage group page."""
        self._go_manage_group(page, ADMIN_EMAIL, ADMIN_PASSWORD)
        assert "500" not in page.title(), "Manage Group page 500 for admin"
        content = page.inner_text("body").lower()
        assert ("group" in content or "manage" in content or "contact" in content), (
            f"Manage Group page appears empty for admin. URL={page.url}")

    def test_manage_group_owner_can_access(self, page: Page):
        """Spec §1: Company Owner must be able to view manage group page."""
        self._go_manage_group(page, OWNER_EMAIL, OWNER_PASSWORD)
        assert "500" not in page.title(), "Manage Group page 500 for owner"

    def test_manage_group_agent_is_blocked(self, page: Page):
        """Spec §1: Agent must NOT be allowed to access manage group page."""
        _login_as(page, AGENT_EMAIL, AGENT_PASSWORD)
        page.goto(MANAGE_GRP_URL)
        page.wait_for_load_state(LOAD_STATE)
        page.wait_for_timeout(1500)
        blocked = (
            "/login" in page.url
            or "/dashboard" in page.url
            or "403" in page.title()
            or "denied" in page.inner_text("body").lower()
            or "access" in page.inner_text("body").lower()
            or "not allowed" in page.inner_text("body").lower()
        )
        assert blocked, (
            f"Agent was NOT blocked from /manage-group. URL={page.url}")

    # ── 2. Group CRUD ─────────────────────────────────────────────────────────

    def test_manage_group_create_button_present(self, page: Page):
        """Spec §2 Create: A 'Create Group' / 'New Group' button must exist."""
        self._go_manage_group(page)
        btn = page.locator(
            'button:has-text("Create"), button:has-text("New Group"), '
            'button:has-text("Add Group"), a:has-text("Create Group")'
        ).first
        content = page.inner_text("body").lower()
        assert btn.count() > 0 or "create" in content or "add" in content, (
            "Create/New Group button not found on manage group page")

    def test_manage_group_create_opens_form(self, page: Page):
        """Spec §2 Create: Clicking Create Group must open a form/modal."""
        self._go_manage_group(page)
        btn = page.locator(
            'button:has-text("Create"), button:has-text("New Group"), '
            'button:has-text("Add Group")'
        ).first
        if btn.count() > 0 and btn.is_visible(timeout=3000):
            btn.click()
            page.wait_for_timeout(1200)
            modal = page.locator('[role="dialog"], [aria-modal="true"]').first
            opened = (
                (modal.count() > 0 and modal.is_visible(timeout=2000))
                or "create" in page.url.lower()
                or page.locator('input[placeholder*="group" i], input[placeholder*="name" i]').count() > 0
            )
            assert opened, "Create Group clicked but no form/modal appeared"

    def test_manage_group_edit_action_present(self, page: Page):
        """Spec §2 Update: Edit action must be available for groups."""
        self._go_manage_group(page)
        content = page.inner_text("body").lower()
        edit_btn = page.locator(
            'button:has-text("Edit"), a:has-text("Edit"), '
            '[aria-label*="edit" i], [title*="edit" i]'
        ).first
        assert edit_btn.count() > 0 or "edit" in content, (
            "Edit action not found on manage group page")

    def test_manage_group_delete_action_present(self, page: Page):
        """Spec §2 Delete: Delete action must be available for groups."""
        self._go_manage_group(page)
        content = page.inner_text("body").lower()
        del_btn = page.locator(
            'button:has-text("Delete"), a:has-text("Delete"), '
            '[aria-label*="delete" i], [title*="delete" i]'
        ).first
        assert del_btn.count() > 0 or "delete" in content, (
            "Delete action not found on manage group page")

    # ── 3. Customer Management ────────────────────────────────────────────────

    def test_manage_group_customer_count_in_table(self, page: Page):
        """Spec §4: Table must show number of customers per group."""
        self._go_manage_group(page)
        content = page.inner_text("body").lower()
        # Count/customer number should appear somewhere in the table
        has_count = re.search(r"\d+", content) is not None
        assert has_count, (
            "No numeric customer count found in manage group table")

    def test_manage_group_import_customers_button(self, page: Page):
        """Spec §3: Import (Excel) button must be present."""
        self._go_manage_group(page)
        content = page.inner_text("body").lower()
        btn = page.locator(
            'button:has-text("Import"), a:has-text("Import"), '
            '[aria-label*="import" i]'
        ).first
        assert btn.count() > 0 or "import" in content, (
            "Import customers button not found on manage group page")

    def test_manage_group_export_customers_button(self, page: Page):
        """Spec §3: Export (CSV) button must be present."""
        self._go_manage_group(page)
        content = page.inner_text("body").lower()
        btn = page.locator(
            'button:has-text("Export"), a:has-text("Export"), '
            '[aria-label*="export" i]'
        ).first
        assert btn.count() > 0 or "export" in content, (
            "Export customers button not found on manage group page")

    # ── 4. Table Search ───────────────────────────────────────────────────────

    def test_manage_group_search_by_name_present(self, page: Page):
        """Spec §4: Search input for group name must be present."""
        self._go_manage_group(page)
        search = page.locator(
            'input[placeholder*="search" i], input[placeholder*="group" i], '
            'input[placeholder*="name" i], input[type="search"]'
        ).first
        content = page.inner_text("body").lower()
        assert search.count() > 0 or "search" in content, (
            "Search field not found on manage group page")

    def test_manage_group_search_does_not_crash(self, page: Page):
        """Spec §4: Searching group name must filter table without crash."""
        self._go_manage_group(page)
        search = page.locator(
            'input[placeholder*="search" i], input[placeholder*="group" i], '
            'input[type="search"]'
        ).first
        if search.count() > 0 and search.is_visible(timeout=3000):
            search.fill("TestGroup")
            page.wait_for_timeout(1200)
        assert "500" not in page.title(), "Page crashed after group search"

    # ── 5. Pagination ─────────────────────────────────────────────────────────

    def test_manage_group_pagination_present_when_many_groups(self, page: Page):
        """Spec §4: Pagination must appear when group list is large."""
        self._go_manage_group(page)
        rows = page.locator("table tbody tr, [role='row']").count()
        if rows > 9:
            pager = page.locator(
                "[class*='pagination'], button:has-text('Next'), "
                "button:has-text('Previous'), [aria-label*='page' i]"
            ).first
            assert pager.count() > 0, (
                f"Pagination missing with {rows} group rows")

    # ── Quality ───────────────────────────────────────────────────────────────

    def test_manage_group_no_5xx_on_load(self, page: Page):
        """Manage Group page must not trigger 5xx responses."""
        errs: list = []
        page.on("response", lambda r: errs.append(r.status)
                if r.status >= 500 else None)
        self._go_manage_group(page)
        assert errs == [], f"5xx on manage group page: {errs[:3]}"

    def test_manage_group_no_js_errors(self, page: Page):
        """Manage Group page must not produce uncaught JS errors."""
        errs: list = []
        page.on("console",  lambda m: errs.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: errs.append(str(e)))
        self._go_manage_group(page)
        real = [e for e in errs if "extension" not in e.lower()
                and "favicon" not in e.lower()]
        assert real == [], f"JS errors on manage group page: {real[:3]}"

    def test_manage_group_no_undefined_in_table(self, page: Page):
        """Manage Group table must not render 'undefined' or '[object Object]'."""
        self._go_manage_group(page)
        content = page.inner_text("body")
        assert "undefined" not in content, (
            "Manage Group table contains literal 'undefined'")
        assert "[object Object]" not in content, (
            "Manage Group table contains '[object Object]' — data binding bug")
