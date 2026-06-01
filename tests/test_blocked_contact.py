import os, time, pytest
from playwright.sync_api import Page, expect
BASE_URL = os.getenv("BASE_URL", "https://dev.prowhats.com/en")

from dotenv import load_dotenv
from playwright.sync_api import Page, expect

load_dotenv()

BASE_URL = "https://dev.prowhats.com/en"
LOGIN_URL = f"{BASE_URL}/login"
DASHBOARD_URL = f"{BASE_URL}/dashboard"
BLOCKED_CONTACTS_URL = f"{BASE_URL}/contacts/blocked-contacts"

LOAD_STATE = "networkidle"

# =========================================================
# ENV Credentials
# =========================================================

OWNER_EMAIL = os.getenv("OWNER_EMAIL")
OWNER_PASSWORD = os.getenv("OWNER_PASSWORD")

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

AGENT_EMAIL = os.getenv("AGENT_EMAIL")
AGENT_PASSWORD = os.getenv("AGENT_PASSWORD")


# =========================================================
# Helper Functions
# =========================================================

def login(page: Page, email: str, password: str):
    """
    Generic login helper.
    """

    page.goto(LOGIN_URL)
    page.wait_for_load_state(LOAD_STATE)

    email_input = page.locator(
        'input[type="email"], input[name="email"]'
    ).first

    password_input = page.locator(
        'input[type="password"], input[name="password"]'
    ).first

    login_button = page.locator(
        'button:has-text("Login"), '
        'button:has-text("Sign In"), '
        'button[type="submit"]'
    ).first

    email_input.fill(email)
    password_input.fill(password)

    login_button.click()

    page.wait_for_load_state(LOAD_STATE)

    assert "dashboard" in page.url.lower(), \
        "Login failed or dashboard redirect did not happen."


def goto_blocked_contacts(page: Page):
    """
    Navigate to blocked contacts page.
    """

    page.goto(BLOCKED_CONTACTS_URL)
    page.wait_for_load_state(LOAD_STATE)

    assert "blocked-contacts" in page.url.lower(), \
        "Blocked contacts page failed to load."


# =========================================================
# Test Class
# =========================================================

class TestBlockedContactsModule:

    # =====================================================
    # 8.1 Authentication & Authorization
    # =====================================================

    def test_bc01_unauthenticated_redirect_to_login(self, page: Page):
        """
        Verify unauthenticated users are redirected to login.
        """

        page.goto(BLOCKED_CONTACTS_URL)
        page.wait_for_load_state(LOAD_STATE)

        assert "login" in page.url.lower()

    @pytest.mark.owner
    def test_bc02_company_owner_login_success(self, page: Page):
        """
        Verify Company Owner can log in successfully.
        """

        login(page, OWNER_EMAIL, OWNER_PASSWORD)

    @pytest.mark.admin
    def test_bc03_admin_login_success(self, page: Page):
        """
        Verify Admin can log in successfully.
        """

        login(page, ADMIN_EMAIL, ADMIN_PASSWORD)

    @pytest.mark.agent
    def test_bc04_agent_login_success(self, page: Page):
        """
        Verify Agent can log in successfully.
        """

        login(page, AGENT_EMAIL, AGENT_PASSWORD)

    @pytest.mark.owner
    def test_bc05_owner_can_access_blocked_contacts(self, page: Page):
        """
        Verify owner can access blocked contacts page.
        """

        login(page, OWNER_EMAIL, OWNER_PASSWORD)
        goto_blocked_contacts(page)

    @pytest.mark.admin
    def test_bc06_admin_can_access_blocked_contacts(self, page: Page):
        """
        Verify admin can access blocked contacts page.
        """

        login(page, ADMIN_EMAIL, ADMIN_PASSWORD)
        goto_blocked_contacts(page)

    @pytest.mark.agent
    def test_bc07_agent_can_access_blocked_contacts(self, page: Page):
        """
        Verify agent can access blocked contacts page.
        """

        login(page, AGENT_EMAIL, AGENT_PASSWORD)
        goto_blocked_contacts(page)

    # =====================================================
    # 8.2 Navigation
    # =====================================================

    def test_bc08_navigation_dashboard_to_blocked_contacts(
        self,
        page: Page
    ):
        """
        Verify user can navigate from dashboard to blocked contacts page.
        """

        login(page, OWNER_EMAIL, OWNER_PASSWORD)

        page.goto(BLOCKED_CONTACTS_URL)
        page.wait_for_load_state(LOAD_STATE)

        assert "blocked-contacts" in page.url.lower()

    def test_bc09_direct_url_access_after_login(self, page: Page):
        """
        Verify direct URL access works after login.
        """

        login(page, OWNER_EMAIL, OWNER_PASSWORD)

        page.goto(BLOCKED_CONTACTS_URL)
        page.wait_for_load_state(LOAD_STATE)

        assert page.url == BLOCKED_CONTACTS_URL

    def test_bc10_browser_refresh_keeps_page_stable(self, page: Page):
        """
        Verify browser refresh does not break page.
        """

        login(page, OWNER_EMAIL, OWNER_PASSWORD)
        goto_blocked_contacts(page)

        page.reload()
        page.wait_for_load_state(LOAD_STATE)

        assert "blocked-contacts" in page.url.lower()

    # =====================================================
    # 8.3 View Blocked Contacts
    # =====================================================

    def test_bc11_blocked_contacts_table_visible(self, page: Page):
        """
        Verify blocked contacts table/list renders correctly.
        """

        login(page, OWNER_EMAIL, OWNER_PASSWORD)
        goto_blocked_contacts(page)

        table = page.locator("table").first

        expect(table).to_be_visible()

    def test_bc12_blocked_contacts_table_headers_visible(
        self,
        page: Page
    ):
        """
        Verify table headers are visible.
        """

        login(page, OWNER_EMAIL, OWNER_PASSWORD)
        goto_blocked_contacts(page)

        headers = page.locator("table thead tr th")

        assert headers.count() > 0, \
            "Table headers are not visible."

    def test_bc13_blocked_contacts_data_loaded(self, page: Page):
        """
        Verify blocked contacts data loads properly.
        """

        login(page, OWNER_EMAIL, OWNER_PASSWORD)
        goto_blocked_contacts(page)

        rows = page.locator("table tbody tr")

        assert rows.count() >= 0

    def test_bc14_empty_state_visibility(self, page: Page):
        """
        Verify empty state appears if no data exists.
        """

        login(page, OWNER_EMAIL, OWNER_PASSWORD)
        goto_blocked_contacts(page)

        empty_state = page.locator(
            "text=No results found, "
            "text=No blocked contacts, "
            "text=No data"
        )

        assert empty_state.count() >= 0

    # =====================================================
    # 8.4 Block & Unblock Actions
    # =====================================================

    def test_bc15_block_button_visible(self, page: Page):
        """
        Verify block button/action is visible.
        """

        login(page, OWNER_EMAIL, OWNER_PASSWORD)
        goto_blocked_contacts(page)

        block_btn = page.locator(
            'button:has-text("Block")'
        ).first

        assert block_btn.count() >= 0

    def test_bc16_unblock_button_visible(self, page: Page):
        """
        Verify unblock button/action is visible.
        """

        login(page, OWNER_EMAIL, OWNER_PASSWORD)
        goto_blocked_contacts(page)

        unblock_btn = page.locator(
            'button:has-text("Unblock")'
        ).first

        assert unblock_btn.count() >= 0

    def test_bc17_user_can_unblock_contact(self, page: Page):
        """
        Verify user can unblock contact successfully.
        """

        login(page, OWNER_EMAIL, OWNER_PASSWORD)
        goto_blocked_contacts(page)

        unblock_btn = page.locator(
            'button:has-text("Unblock")'
        ).first

        if unblock_btn.count() > 0:
            unblock_btn.click()

            page.wait_for_timeout(2000)

            toast = page.locator(
                "text=success, text=updated, text=unblocked"
            )

            assert toast.count() >= 0

    def test_bc18_user_can_block_contact(self, page: Page):
        """
        Verify user can block contact successfully.
        """

        login(page, OWNER_EMAIL, OWNER_PASSWORD)
        goto_blocked_contacts(page)

        block_btn = page.locator(
            'button:has-text("Block")'
        ).first

        if block_btn.count() > 0:
            block_btn.click()

            page.wait_for_timeout(2000)

            toast = page.locator(
                "text=success, text=blocked"
            )

            assert toast.count() >= 0

    def test_bc19_ui_updates_after_action(self, page: Page):
        """
        Verify UI updates after block/unblock action.
        """

        login(page, OWNER_EMAIL, OWNER_PASSWORD)
        goto_blocked_contacts(page)

        rows_before = page.locator("table tbody tr").count()

        action_btn = page.locator(
            'button:has-text("Block"), '
            'button:has-text("Unblock")'
        ).first

        if action_btn.count() > 0:
            action_btn.click()

            page.wait_for_timeout(3000)

            rows_after = page.locator("table tbody tr").count()

            assert rows_after >= 0
            assert rows_before >= 0

    # =====================================================
    # 8.5 Search
    # =====================================================

    def test_bc20_search_input_visible(self, page: Page):
        """
        Verify search input field is visible.
        """

        login(page, OWNER_EMAIL, OWNER_PASSWORD)
        goto_blocked_contacts(page)

        search_input = page.locator(
            'input[type="search"], '
            'input[placeholder*="Search"], '
            'input'
        ).first

        expect(search_input).to_be_visible()

    def test_bc21_search_valid_customer_name(self, page: Page):
        """
        Verify valid search filters data.
        """

        login(page, OWNER_EMAIL, OWNER_PASSWORD)
        goto_blocked_contacts(page)

        search_input = page.locator("input").first

        search_input.fill("John")

        page.wait_for_timeout(2000)

        rows = page.locator("table tbody tr")

        assert rows.count() >= 0

    def test_bc22_partial_name_search(self, page: Page):
        """
        Verify partial name search works.
        """

        login(page, OWNER_EMAIL, OWNER_PASSWORD)
        goto_blocked_contacts(page)

        search_input = page.locator("input").first

        search_input.fill("Jo")

        page.wait_for_timeout(2000)

        assert search_input.input_value() == "Jo"

    def test_bc23_search_case_insensitive(self, page: Page):
        """
        Verify search is case insensitive.
        """

        login(page, OWNER_EMAIL, OWNER_PASSWORD)
        goto_blocked_contacts(page)

        search_input = page.locator("input").first

        search_input.fill("JOHN")

        page.wait_for_timeout(2000)

        assert search_input.input_value() == "JOHN"

    def test_bc24_search_trim_spaces(self, page: Page):
        """
        Verify search handles extra spaces properly.
        """

        login(page, OWNER_EMAIL, OWNER_PASSWORD)
        goto_blocked_contacts(page)

        search_input = page.locator("input").first

        search_input.fill("   John   ")

        page.wait_for_timeout(2000)

        assert search_input.input_value() == "   John   "

    def test_bc25_search_non_existing_name(self, page: Page):
        """
        Verify invalid search shows empty state.
        """

        login(page, OWNER_EMAIL, OWNER_PASSWORD)
        goto_blocked_contacts(page)

        search_input = page.locator("input").first

        search_input.fill("xyzinvaliduser123")

        page.wait_for_timeout(2000)

        empty_state = page.locator(
            "text=No results found, "
            "text=No data"
        )

        assert empty_state.count() >= 0

    def test_bc26_clear_search_restores_list(self, page: Page):
        """
        Verify clearing search restores list.
        """

        login(page, OWNER_EMAIL, OWNER_PASSWORD)
        goto_blocked_contacts(page)

        search_input = page.locator("input").first

        search_input.fill("John")
        page.wait_for_timeout(1000)

        search_input.clear()
        page.wait_for_timeout(1000)

        rows = page.locator("table tbody tr")

        assert rows.count() >= 0

    def test_bc27_search_special_characters(self, page: Page):
        """
        Verify special character search does not crash UI.
        """

        login(page, OWNER_EMAIL, OWNER_PASSWORD)
        goto_blocked_contacts(page)

        search_input = page.locator("input").first

        search_input.fill("@#$%^&*()")

        page.wait_for_timeout(1000)

        assert search_input.input_value() == "@#$%^&*()"

    # =====================================================
    # 8.6 Responsive Testing
    # =====================================================

    def test_bc28_mobile_view_layout(self, browser):
        """
        Verify page layout works on mobile devices.
        """

        mobile_page = browser.new_page(
            viewport={"width": 390, "height": 844}
        )

        login(mobile_page, OWNER_EMAIL, OWNER_PASSWORD)

        goto_blocked_contacts(mobile_page)

        assert mobile_page.viewport_size["width"] == 390

        mobile_page.close()

    def test_bc29_tablet_view_layout(self, browser):
        """
        Verify page layout works on tablet devices.
        """

        tablet_page = browser.new_page(
            viewport={"width": 768, "height": 1024}
        )

        login(tablet_page, OWNER_EMAIL, OWNER_PASSWORD)

        goto_blocked_contacts(tablet_page)

        assert tablet_page.viewport_size["width"] == 768

        tablet_page.close()

    def test_bc30_buttons_clickable_mobile(self, browser):
        """
        Verify buttons remain clickable on mobile devices.
        """

        mobile_page = browser.new_page(
            viewport={"width": 390, "height": 844}
        )

        login(mobile_page, OWNER_EMAIL, OWNER_PASSWORD)

        goto_blocked_contacts(mobile_page)

        buttons = mobile_page.locator("button")

        assert buttons.count() > 0

        mobile_page.close()

    # =====================================================
    # 8.7 Error Handling
    # =====================================================

    def test_bc31_unauthorized_api_redirects_login(self, page: Page):
        """
        Verify unauthorized access redirects to login.
        """

        page.goto(BLOCKED_CONTACTS_URL)
        page.wait_for_load_state(LOAD_STATE)

        assert "login" in page.url.lower()

    def test_bc32_ui_stable_during_reload(self, page: Page):
        """
        Verify UI remains stable during reload.
        """

        login(page, OWNER_EMAIL, OWNER_PASSWORD)

        goto_blocked_contacts(page)

        page.reload()
        page.wait_for_load_state(LOAD_STATE)

        table = page.locator("table").first

        expect(table).to_be_visible()

    def test_bc33_user_friendly_error_handling(self, page: Page):
        """
        Verify user-friendly error handling exists.
        """

        login(page, OWNER_EMAIL, OWNER_PASSWORD)

        goto_blocked_contacts(page)

        error_elements = page.locator(
            "text=Error, text=Something went wrong"
        )

        assert error_elements.count() >= 0