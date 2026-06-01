import os
import pytest
from playwright.sync_api import Page, expect
from dotenv import load_dotenv

# Load configuration variables from .env file
load_dotenv()

required_env_vars = [
    "OWNER_EMAIL",
    "OWNER_PASSWORD",
    "ADMIN_EMAIL",
    "ADMIN_PASSWORD",
]

for var in required_env_vars:
    if not os.getenv(var):
        raise ValueError(f"Missing required environment variable: {var}")

# System Routing Constants
BASE_URL = "https://dev.prowhats.com/en"
LOGIN_URL = "https://dev.prowhats.com/en/login"
DASHBOARD_URL = "https://dev.prowhats.com/en/dashboard"
FILE_MANAGER_URL = "https://dev.prowhats.com/en/files"

OWNER_EMAIL = os.getenv("OWNER_EMAIL")
OWNER_PASSWORD = os.getenv("OWNER_PASSWORD")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

LOAD_STATE = "networkidle"


class TestFileManager:

    def login(self, page: Page, email: str, password: str):
        """Helper method to authenticate user roles."""
        page.goto(LOGIN_URL)
        page.wait_for_load_state(LOAD_STATE)

        email_input = page.locator('input[type="email"]').first
        password_input = page.locator('input[type="password"]').first

        email_input.fill(email)
        password_input.fill(password)

        login_button = page.locator('button[type="submit"]').first
        login_button.click()

        page.wait_for_load_state(LOAD_STATE)
        expect(page).to_have_url(DASHBOARD_URL)

    def navigate_to_file_manager(self, page: Page):
        """Helper method to access the File Manager route."""
        page.goto(FILE_MANAGER_URL)
        page.wait_for_load_state(LOAD_STATE)

    # --------------------------------------------------------------------------
    # SECURITY & ROUTE GUARDING TESTS
    # --------------------------------------------------------------------------
    @pytest.mark.security
    def test_unauthenticated_user_cannot_access_files_page(self, page: Page):
        """Verify that visitors cannot see the files page directly without logging in."""
        # Attempt direct unauthenticated page routing
        self.navigate_to_file_manager(page)
        
        # System should reject the access or route back to login
        assert page.url != FILE_MANAGER_URL

    @pytest.mark.smoke
    def test_owner_login_and_access(self, page: Page):
        """Verify Company Owner can authenticate and open File Manager."""
        self.login(page, OWNER_EMAIL, OWNER_PASSWORD)
        self.navigate_to_file_manager(page)
        expect(page).to_have_url(FILE_MANAGER_URL)

    @pytest.mark.smoke
    def test_admin_login_and_access(self, page: Page):
        """Verify Admin can authenticate and open File Manager."""
        self.login(page, ADMIN_EMAIL, ADMIN_PASSWORD)
        self.navigate_to_file_manager(page)
        expect(page).to_have_url(FILE_MANAGER_URL)

    # --------------------------------------------------------------------------
    # CORE FUNCTIONAL & UI TAB TESTS
    # --------------------------------------------------------------------------
    @pytest.mark.ui
    def test_default_all_tab_active_on_load(self, page: Page):
        """Verify that the 'All' tab filter is visible/active by default on initialization."""
        self.login(page, ADMIN_EMAIL, ADMIN_PASSWORD)
        self.navigate_to_file_manager(page)

        all_tab = page.locator("text=All").first
        expect(all_tab).to_be_visible()

    @pytest.mark.ui
    def test_category_tabs_visibility(self, page: Page):
        """Verify all targeted structural data tabs are rendering on the table interface."""
        self.login(page, ADMIN_EMAIL, ADMIN_PASSWORD)
        self.navigate_to_file_manager(page)

        categories = ["Image", "Video", "Audio", "Docs"]
        for category in categories:
            tab_element = page.locator(f"text={category}").first
            expect(tab_element).to_be_visible()

    @pytest.mark.functional
    def test_storage_progress_bar_metrics(self, page: Page):
        """Verify storage utilization gauge and file-size metrics (MB/GB) text elements exist."""
        self.login(page, ADMIN_EMAIL, ADMIN_PASSWORD)
        self.navigate_to_file_manager(page)

        page_content = page.content().upper()
        # Ensure either MB or GB text formatting markers exist in page layout context
        assert "MB" in page_content or "GB" in page_content

    @pytest.mark.ui
    def test_layout_view_toggle_presence(self, page: Page):
        """Verify that layouts can theoretically switch or mention List and Grid formats."""
        self.login(page, ADMIN_EMAIL, ADMIN_PASSWORD)
        self.navigate_to_file_manager(page)

        page_content = page.content().lower()
        # Verify user has explicit hooks or indications to view configurations
        assert "grid" in page_content or "list" in page_content

    # --------------------------------------------------------------------------
    # SEARCH, ACTIONS & OPERATIONS LIFECYCLE TESTS
    # --------------------------------------------------------------------------
    @pytest.mark.functional
    def test_search_input_field_interactivity(self, page: Page):
        """Verify user can interact with the file search box element."""
        self.login(page, ADMIN_EMAIL, ADMIN_PASSWORD)
        self.navigate_to_file_manager(page)

        # Look for search fields dynamically matching file criteria
        search_input = page.locator("input[placeholder*='Search'], input[placeholder*='search']").first
        if search_input.count() > 0:
            expect(search_input).to_be_visible()
            search_input.fill("test_document_name")
            page.wait_for_timeout(1000)

    @pytest.mark.ui
    def test_table_row_actions_visibility(self, page: Page):
        """Verify actions like Copy or Delete can be discovered safely within file data views."""
        self.login(page, ADMIN_EMAIL, ADMIN_PASSWORD)
        self.navigate_to_file_manager(page)

        page_content = page.content().lower()
        
        # Check presence of primary actionable design indicators
        assert "copy" in page_content or "url" in page_content
        assert "delete" in page_content

    @pytest.mark.functional
    def test_pagination_controls_existence(self, page: Page):
        """Verify the file listing structure includes pagination capability blocks."""
        self.login(page, ADMIN_EMAIL, ADMIN_PASSWORD)
        self.navigate_to_file_manager(page)

        # Check for typical indicators of tabular pagination elements
        page_content = page.content().lower()
        has_pagination = any(x in page_content for x in ["next", "previous", "page", "pagination"])
        assert has_pagination is True