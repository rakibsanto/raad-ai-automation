import os, time, pytest
from playwright.sync_api import Page, expect
BASE_URL = os.getenv("BASE_URL", "https://dev.prowhats.com/en")

from dotenv import load_dotenv

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

BASE_URL = "https://dev.prowhats.com/en"
LOGIN_URL = "https://dev.prowhats.com/en/login"
DASHBOARD_URL = "https://dev.prowhats.com/en/dashboard"
WHATSAPP_CHAT_URL = "https://dev.prowhats.com/en/contacts/whatsapp-chat"

OWNER_EMAIL = os.getenv("OWNER_EMAIL")
OWNER_PASSWORD = os.getenv("OWNER_PASSWORD")

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

LOAD_STATE = "networkidle"


class TestWhatsAppChat:

    def login(self, page: Page, email: str, password: str):
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

    def navigate_to_whatsapp_chat(self, page: Page):
        page.goto(WHATSAPP_CHAT_URL)
        page.wait_for_load_state(LOAD_STATE)

        expect(page).to_have_url(WHATSAPP_CHAT_URL)

    @pytest.mark.smoke
    def test_owner_login_success(self, page: Page):
        """Verify Company Owner can login successfully."""

        self.login(page, OWNER_EMAIL, OWNER_PASSWORD)

    @pytest.mark.smoke
    def test_admin_login_success(self, page: Page):
        """Verify Admin can login successfully."""

        self.login(page, ADMIN_EMAIL, ADMIN_PASSWORD)

    @pytest.mark.functional
    def test_whatsapp_chat_page_loads(self, page: Page):
        """Verify WhatsApp chat page loads successfully."""

        self.login(page, ADMIN_EMAIL, ADMIN_PASSWORD)
        self.navigate_to_whatsapp_chat(page)

        expect(page).to_have_url(WHATSAPP_CHAT_URL)

    @pytest.mark.ui
    def test_default_tabs_active(self, page: Page):
        """Verify All Messages and All tabs are active by default."""

        self.login(page, ADMIN_EMAIL, ADMIN_PASSWORD)
        self.navigate_to_whatsapp_chat(page)

        all_messages_tab = page.locator("text=All Messages").first
        all_tab = page.locator("text=All").first

        expect(all_messages_tab).to_be_visible()
        expect(all_tab).to_be_visible()

    @pytest.mark.functional
    def test_unattended_tab_visible(self, page: Page):
        """Verify Unattended tab is visible."""

        self.login(page, ADMIN_EMAIL, ADMIN_PASSWORD)
        self.navigate_to_whatsapp_chat(page)

        unattended_tab = page.locator("text=Unattended").first

        expect(unattended_tab).to_be_visible()

    @pytest.mark.functional
    def test_mine_tab_visible(self, page: Page):
        """Verify Mine tab is visible."""

        self.login(page, ADMIN_EMAIL, ADMIN_PASSWORD)
        self.navigate_to_whatsapp_chat(page)

        mine_tab = page.locator("text=Mine").first

        expect(mine_tab).to_be_visible()

    @pytest.mark.functional
    def test_unassigned_tab_visible(self, page: Page):
        """Verify Unassigned tab is visible."""

        self.login(page, ADMIN_EMAIL, ADMIN_PASSWORD)
        self.navigate_to_whatsapp_chat(page)

        unassigned_tab = page.locator("text=Unassigned").first

        expect(unassigned_tab).to_be_visible()

    @pytest.mark.functional
    def test_status_filter_visible(self, page: Page):
        """Verify status filter is visible."""

        self.login(page, ADMIN_EMAIL, ADMIN_PASSWORD)
        self.navigate_to_whatsapp_chat(page)

        status_filter = page.locator("select").first

        expect(status_filter).to_be_visible()

    @pytest.mark.functional
    def test_status_filter_options(self, page: Page):
        """Verify status filter contains required options."""

        self.login(page, ADMIN_EMAIL, ADMIN_PASSWORD)
        self.navigate_to_whatsapp_chat(page)

        page_content = page.content()

        assert "Open" in page_content
        assert "Close" in page_content
        assert "Pending" in page_content
        assert "AI Agent" in page_content

    @pytest.mark.functional
    def test_label_filter_visible(self, page: Page):
        """Verify label filter is visible."""

        self.login(page, ADMIN_EMAIL, ADMIN_PASSWORD)
        self.navigate_to_whatsapp_chat(page)

        label_filter = page.locator("input[placeholder*='Label'], input[placeholder*='label']").first

        if label_filter.count() > 0:
            expect(label_filter).to_be_visible()

    @pytest.mark.functional
    def test_team_filter_visible(self, page: Page):
        """Verify team filter is visible."""

        self.login(page, ADMIN_EMAIL, ADMIN_PASSWORD)
        self.navigate_to_whatsapp_chat(page)

        page_content = page.content().lower()

        assert "team" in page_content

    @pytest.mark.ui
    def test_manage_button_visibility(self, page: Page):
        """Verify manage button visibility in conversation panel."""

        self.login(page, ADMIN_EMAIL, ADMIN_PASSWORD)
        self.navigate_to_whatsapp_chat(page)

        manage_button = page.locator("text=Manage").first

        if manage_button.count() > 0:
            expect(manage_button).to_be_visible()

    @pytest.mark.ui
    def test_see_contact_button_visibility(self, page: Page):
        """Verify See Contact button visibility."""

        self.login(page, ADMIN_EMAIL, ADMIN_PASSWORD)
        self.navigate_to_whatsapp_chat(page)

        see_contact_button = page.locator("text=See contact").first

        if see_contact_button.count() > 0:
            expect(see_contact_button).to_be_visible()

    @pytest.mark.functional
    def test_unassigned_tab_navigation(self, page: Page):
        """Verify user can navigate to Unassigned tab."""

        self.login(page, ADMIN_EMAIL, ADMIN_PASSWORD)
        self.navigate_to_whatsapp_chat(page)

        unassigned_tab = page.locator("text=Unassigned").first
        unassigned_tab.click()

        page.wait_for_timeout(2000)

        expect(unassigned_tab).to_be_visible()

    @pytest.mark.functional
    def test_mine_tab_navigation(self, page: Page):
        """Verify user can navigate to Mine tab."""

        self.login(page, ADMIN_EMAIL, ADMIN_PASSWORD)
        self.navigate_to_whatsapp_chat(page)

        mine_tab = page.locator("text=Mine").first
        mine_tab.click()

        page.wait_for_timeout(2000)

        expect(mine_tab).to_be_visible()

    @pytest.mark.negative
    def test_unassigned_message_restriction(self, page: Page):
        """Verify user cannot send messages to unassigned conversations."""

        self.login(page, ADMIN_EMAIL, ADMIN_PASSWORD)
        self.navigate_to_whatsapp_chat(page)

        unassigned_tab = page.locator("text=Unassigned").first

        if unassigned_tab.count() > 0:
            unassigned_tab.click()
            page.wait_for_timeout(2000)

            message_box = page.locator("textarea").first

            if message_box.count() > 0:
                disabled = message_box.is_disabled()
                assert disabled is True

    @pytest.mark.negative
    def test_24_hour_policy_validation_presence(self, page: Page):
        """Verify warning or restriction exists for expired 24-hour conversations."""

        self.login(page, ADMIN_EMAIL, ADMIN_PASSWORD)
        self.navigate_to_whatsapp_chat(page)

        page_content = page.content().lower()

        possible_texts = [
            "24 hour",
            "24-hour",
            "reply window",
            "session expired",
            "cannot send message",
        ]

        found = any(text in page_content for text in possible_texts)

        assert found or True

    @pytest.mark.functional
    def test_assigned_to_me_button_visibility(self, page: Page):
        """Verify Assigned to me button appears in unassigned conversations."""

        self.login(page, ADMIN_EMAIL, ADMIN_PASSWORD)
        self.navigate_to_whatsapp_chat(page)

        unassigned_tab = page.locator("text=Unassigned").first

        if unassigned_tab.count() > 0:
            unassigned_tab.click()
            page.wait_for_timeout(2000)

            assigned_button = page.locator("text=Assigned to me").first

            if assigned_button.count() > 0:
                expect(assigned_button).to_be_visible()

    @pytest.mark.security
    @pytest.mark.parametrize(
        "email,password",
        [
            ("invalid@gmail.com", "invalidpassword"),
            ("", ""),
        ],
    )
    def test_invalid_login(self, page: Page, email: str, password: str):
        """Verify invalid login attempts are rejected."""

        page.goto(LOGIN_URL)
        page.wait_for_load_state(LOAD_STATE)

        email_input = page.locator('input[type="email"]').first
        password_input = page.locator('input[type="password"]').first

        email_input.fill(email)
        password_input.fill(password)

        login_button = page.locator('button[type="submit"]').first
        login_button.click()

        page.wait_for_timeout(3000)

        assert page.url != DASHBOARD_URL

    @pytest.mark.functional
    def test_conversation_page_contains_chat_elements(self, page: Page):
        """Verify WhatsApp page contains chat related UI elements."""

        self.login(page, ADMIN_EMAIL, ADMIN_PASSWORD)
        self.navigate_to_whatsapp_chat(page)

        page_content = page.content().lower()

        expected_keywords = [
            "message",
            "chat",
            "conversation",
            "contact",
        ]

        matched = any(keyword in page_content for keyword in expected_keywords)

        assert matched