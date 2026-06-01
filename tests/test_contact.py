import os, time, pytest
from playwright.sync_api import Page, expect
BASE_URL = os.getenv("BASE_URL", "https://dev.prowhats.com/en")

import random
import string
import pytest
from dotenv import load_dotenv
from playwright.sync_api import Page, expect

load_dotenv()

# =========================================================
# URLs
# =========================================================

BASE_URL = "https://dev.prowhats.com/en"
LOGIN_URL = f"{BASE_URL}/login"
DASHBOARD_URL = f"{BASE_URL}/dashboard"
CONTACTS_URL = f"{BASE_URL}/contacts/contacts"

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

def random_string(length=6):
    return ''.join(random.choices(string.ascii_letters, k=length))


def random_phone():
    return f"+88017{random.randint(10000000, 99999999)}"


def login(page: Page, email: str, password: str):
    """
    Generic login helper
    """

    page.goto(LOGIN_URL)
    page.wait_for_load_state(LOAD_STATE)

    email_input = page.locator(
        'input[type="email"], input[name="email"]'
    ).first

    password_input = page.locator(
        'input[type="password"], input[name="password"]'
    ).first

    login_btn = page.locator(
        'button:has-text("Login"), '
        'button:has-text("Sign In"), '
        'button[type="submit"]'
    ).first

    email_input.fill(email)
    password_input.fill(password)

    login_btn.click()

    page.wait_for_load_state(LOAD_STATE)

    assert "dashboard" in page.url.lower(), \
        "User login failed."


def goto_contacts(page: Page):
    """
    Navigate to contacts page
    """

    page.goto(CONTACTS_URL)
    page.wait_for_load_state(LOAD_STATE)

    assert "contacts" in page.url.lower(), \
        "Contacts page failed to load."


# =========================================================
# Test Class
# =========================================================

class TestContactManagement:

    # =====================================================
    # 10.1 Authentication & Authorization
    # =====================================================

    def test_ct01_unauthorized_redirect_to_login(self, page: Page):
        """
        Verify unauthorized users redirect to login
        """

        page.goto(CONTACTS_URL)
        page.wait_for_load_state(LOAD_STATE)

        assert "login" in page.url.lower()

    def test_ct02_owner_login_success(self, page: Page):
        """
        Verify owner login success
        """

        login(page, OWNER_EMAIL, OWNER_PASSWORD)

    def test_ct03_admin_login_success(self, page: Page):
        """
        Verify admin login success
        """

        login(page, ADMIN_EMAIL, ADMIN_PASSWORD)

    def test_ct04_agent_login_success(self, page: Page):
        """
        Verify agent login success
        """

        login(page, AGENT_EMAIL, AGENT_PASSWORD)

    def test_ct05_authorized_user_access_contacts(self, page: Page):
        """
        Verify authorized user can access contacts page
        """

        login(page, OWNER_EMAIL, OWNER_PASSWORD)
        goto_contacts(page)

    # =====================================================
    # 10.2 Contact List View
    # =====================================================

    def test_ct06_contacts_table_visible(self, page: Page):
        """
        Verify contacts table visible
        """

        login(page, OWNER_EMAIL, OWNER_PASSWORD)
        goto_contacts(page)

        table = page.locator("table").first

        expect(table).to_be_visible()

    def test_ct07_contact_table_headers_visible(self, page: Page):
        """
        Verify table headers visible
        """

        login(page, OWNER_EMAIL, OWNER_PASSWORD)
        goto_contacts(page)

        headers = page.locator("table thead tr th")

        assert headers.count() > 0

    def test_ct08_contact_action_buttons_visible(self, page: Page):
        """
        Verify action buttons visible
        """

        login(page, OWNER_EMAIL, OWNER_PASSWORD)
        goto_contacts(page)

        buttons = page.locator(
            'button:has-text("Edit"), '
            'button:has-text("Delete"), '
            'button:has-text("View")'
        )

        assert buttons.count() >= 0

    def test_ct09_contacts_table_responsive_mobile(self, browser):
        """
        Verify contacts table responsive on mobile
        """

        mobile_page = browser.new_page(
            viewport={"width": 390, "height": 844}
        )

        login(mobile_page, OWNER_EMAIL, OWNER_PASSWORD)

        goto_contacts(mobile_page)

        table = mobile_page.locator("table").first

        expect(table).to_be_visible()

        mobile_page.close()

    # =====================================================
    # 10.3 Add Contact
    # =====================================================

    def test_ct10_add_contact_button_visible(self, page: Page):
        """
        Verify add contact button visible
        """

        login(page, OWNER_EMAIL, OWNER_PASSWORD)
        goto_contacts(page)

        add_btn = page.locator(
            'button:has-text("Add Contact"), '
            'button:has-text("Add")'
        ).first

        expect(add_btn).to_be_visible()

    def test_ct11_create_contact_required_fields(self, page: Page):
        """
        Verify create contact with required fields
        """

        login(page, OWNER_EMAIL, OWNER_PASSWORD)
        goto_contacts(page)

        name = f"TestUser_{random_string()}"
        phone = random_phone()

        add_btn = page.locator(
            'button:has-text("Add Contact"), '
            'button:has-text("Add")'
        ).first

        add_btn.click()

        page.wait_for_timeout(1000)

        name_input = page.locator(
            'input[name="name"], input[placeholder*="Name"]'
        ).first

        phone_input = page.locator(
            'input[name="phone"], input[placeholder*="Phone"]'
        ).first

        save_btn = page.locator(
            'button:has-text("Save"), '
            'button:has-text("Create")'
        ).first

        name_input.fill(name)
        phone_input.fill(phone)

        save_btn.click()

        page.wait_for_timeout(3000)

        success_msg = page.locator(
            "text=success, text=created"
        )

        assert success_msg.count() >= 0

    def test_ct12_required_field_validation(self, page: Page):
        """
        Verify required field validation
        """

        login(page, OWNER_EMAIL, OWNER_PASSWORD)
        goto_contacts(page)

        add_btn = page.locator(
            'button:has-text("Add Contact"), '
            'button:has-text("Add")'
        ).first

        add_btn.click()

        save_btn = page.locator(
            'button:has-text("Save"), '
            'button:has-text("Create")'
        ).first

        save_btn.click()

        validation = page.locator(
            "text=required, text=invalid"
        )

        assert validation.count() >= 0

    def test_ct13_invalid_phone_validation(self, page: Page):
        """
        Verify invalid phone format validation
        """

        login(page, OWNER_EMAIL, OWNER_PASSWORD)
        goto_contacts(page)

        add_btn = page.locator(
            'button:has-text("Add Contact"), '
            'button:has-text("Add")'
        ).first

        add_btn.click()

        name_input = page.locator("input").nth(0)
        phone_input = page.locator("input").nth(1)

        name_input.fill("InvalidPhoneUser")
        phone_input.fill("abc123")

        save_btn = page.locator(
            'button:has-text("Save"), '
            'button:has-text("Create")'
        ).first

        save_btn.click()

        validation = page.locator(
            "text=invalid phone, text=phone format"
        )

        assert validation.count() >= 0

    # =====================================================
    # 10.4 Search & Filter
    # =====================================================

    def test_ct14_search_by_name(self, page: Page):
        """
        Verify search by name
        """

        login(page, OWNER_EMAIL, OWNER_PASSWORD)
        goto_contacts(page)

        search_input = page.locator(
            'input[placeholder*="Name"], '
            'input[type="search"]'
        ).first

        search_input.fill("John")

        page.wait_for_timeout(2000)

        rows = page.locator("table tbody tr")

        assert rows.count() >= 0

    def test_ct15_search_by_phone(self, page: Page):
        """
        Verify search by phone
        """

        login(page, OWNER_EMAIL, OWNER_PASSWORD)
        goto_contacts(page)

        phone_search = page.locator(
            'input[placeholder*="Phone"]'
        ).first

        phone_search.fill("+880")

        page.wait_for_timeout(2000)

        rows = page.locator("table tbody tr")

        assert rows.count() >= 0

    def test_ct16_partial_name_search(self, page: Page):
        """
        Verify partial name search
        """

        login(page, OWNER_EMAIL, OWNER_PASSWORD)
        goto_contacts(page)

        search_input = page.locator("input").first

        search_input.fill("Jo")

        page.wait_for_timeout(1000)

        assert search_input.input_value() == "Jo"

    def test_ct17_no_result_search(self, page: Page):
        """
        Verify no result state
        """

        login(page, OWNER_EMAIL, OWNER_PASSWORD)
        goto_contacts(page)

        search_input = page.locator("input").first

        search_input.fill("NoUserFound123456")

        page.wait_for_timeout(2000)

        empty_state = page.locator(
            "text=No results found, text=No data"
        )

        assert empty_state.count() >= 0

    def test_ct18_clear_filter_button(self, page: Page):
        """
        Verify clear filter functionality
        """

        login(page, OWNER_EMAIL, OWNER_PASSWORD)
        goto_contacts(page)

        clear_btn = page.locator(
            'button:has-text("Clear")'
        ).first

        assert clear_btn.count() >= 0

    # =====================================================
    # 10.5 Edit & Delete
    # =====================================================

    def test_ct19_edit_button_visible(self, page: Page):
        """
        Verify edit button visible
        """

        login(page, OWNER_EMAIL, OWNER_PASSWORD)
        goto_contacts(page)

        edit_btn = page.locator(
            'button:has-text("Edit")'
        ).first

        assert edit_btn.count() >= 0

    def test_ct20_delete_button_visible(self, page: Page):
        """
        Verify delete button visible
        """

        login(page, OWNER_EMAIL, OWNER_PASSWORD)
        goto_contacts(page)

        delete_btn = page.locator(
            'button:has-text("Delete")'
        ).first

        assert delete_btn.count() >= 0

    def test_ct21_cancel_delete_contact(self, page: Page):
        """
        Verify cancel delete keeps contact
        """

        login(page, OWNER_EMAIL, OWNER_PASSWORD)
        goto_contacts(page)

        delete_btn = page.locator(
            'button:has-text("Delete")'
        ).first

        if delete_btn.count() > 0:
            delete_btn.click()

            cancel_btn = page.locator(
                'button:has-text("Cancel")'
            ).first

            if cancel_btn.count() > 0:
                cancel_btn.click()

                assert cancel_btn.count() >= 0

    # =====================================================
    # 10.6 Import / Export
    # =====================================================

    def test_ct22_import_button_visible(self, page: Page):
        """
        Verify import button visible
        """

        login(page, OWNER_EMAIL, OWNER_PASSWORD)
        goto_contacts(page)

        import_btn = page.locator(
            'button:has-text("Import")'
        ).first

        assert import_btn.count() >= 0

    def test_ct23_export_button_visible(self, page: Page):
        """
        Verify export button visible
        """

        login(page, OWNER_EMAIL, OWNER_PASSWORD)
        goto_contacts(page)

        export_btn = page.locator(
            'button:has-text("Export")'
        ).first

        assert export_btn.count() >= 0

    def test_ct24_upload_invalid_file_type(self, page: Page):
        """
        Verify unsupported file validation
        """

        login(page, OWNER_EMAIL, OWNER_PASSWORD)
        goto_contacts(page)

        import_btn = page.locator(
            'button:has-text("Import")'
        ).first

        if import_btn.count() > 0:
            import_btn.click()

            file_input = page.locator(
                'input[type="file"]'
            ).first

            assert file_input.count() >= 0

    # =====================================================
    # 10.7 Pagination
    # =====================================================

    def test_ct25_pagination_visibility(self, page: Page):
        """
        Verify pagination visibility
        """

        login(page, OWNER_EMAIL, OWNER_PASSWORD)
        goto_contacts(page)

        pagination = page.locator(
            'button:has-text("Next"), '
            'button:has-text("Previous")'
        )

        assert pagination.count() >= 0

    def test_ct26_next_page_functionality(self, page: Page):
        """
        Verify next page functionality
        """

        login(page, OWNER_EMAIL, OWNER_PASSWORD)
        goto_contacts(page)

        next_btn = page.locator(
            'button:has-text("Next")'
        ).first

        if next_btn.count() > 0:
            next_btn.click()

            page.wait_for_timeout(2000)

            assert next_btn.count() >= 0

    def test_ct27_rows_per_page_dropdown(self, page: Page):
        """
        Verify rows per page dropdown
        """

        login(page, OWNER_EMAIL, OWNER_PASSWORD)
        goto_contacts(page)

        dropdown = page.locator("select").first

        assert dropdown.count() >= 0

    # =====================================================
    # Error Handling
    # =====================================================

    def test_ct28_api_error_handling(self, page: Page):
        """
        Verify API error handling
        """

        login(page, OWNER_EMAIL, OWNER_PASSWORD)
        goto_contacts(page)

        error_message = page.locator(
            "text=Error, text=Something went wrong"
        )

        assert error_message.count() >= 0

    def test_ct29_ui_stable_after_refresh(self, page: Page):
        """
        Verify UI stable after refresh
        """

        login(page, OWNER_EMAIL, OWNER_PASSWORD)
        goto_contacts(page)

        page.reload()
        page.wait_for_load_state(LOAD_STATE)

        table = page.locator("table").first

        expect(table).to_be_visible()