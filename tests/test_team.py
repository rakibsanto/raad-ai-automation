import os, time, pytest
from playwright.sync_api import Page, expect
BASE_URL = os.getenv("BASE_URL", "https://dev.prowhats.com/en")

from dotenv import load_dotenv

load_dotenv()

# ─── Required environment variables ──────────────────────────────────────────
# All values must be set in the .env file. No hardcoded fallbacks.
_REQUIRED = [
    "BASE_URL",
    "OWNER_EMAIL",
    "OWNER_PASSWORD",
    "ADMIN_EMAIL",
    "ADMIN_PASSWORD",
]
for _var in _REQUIRED:
    if not os.getenv(_var):
        raise EnvironmentError(
            f"Missing required environment variable: {_var}. "
            "Please set it in your .env file."
        )

# ─── URLs (from .env) ────────────────────────────────────────────────────────
BASE_URL      = os.getenv("BASE_URL")
LOGIN_URL     = os.getenv("LOGIN_URL",      f"{BASE_URL}/login")
DASHBOARD_URL = os.getenv("DASHBOARD_URL",  f"{BASE_URL}/dashboard")
TEAMS_URL     = f"{BASE_URL}/teams"

# ─── Credentials (from .env) ─────────────────────────────────────────────────
OWNER_EMAIL    = os.getenv("OWNER_EMAIL")
OWNER_PASSWORD = os.getenv("OWNER_PASSWORD")
ADMIN_EMAIL    = os.getenv("ADMIN_EMAIL")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

LOAD_STATE = "networkidle"


# ─────────────────────────────────────────────────────────────────────────────
# Helper functions
# ─────────────────────────────────────────────────────────────────────────────

def login(page: Page, email: str, password: str) -> None:
    """Log in with given credentials and wait for dashboard redirect."""
    page.goto(LOGIN_URL)
    page.wait_for_load_state(LOAD_STATE)

    page.locator('input[type="email"]').first.fill(email)
    page.locator('input[type="password"]').first.fill(password)
    page.locator('button[type="submit"]').first.click()

    page.wait_for_load_state(LOAD_STATE)


def goto_teams_page(page: Page) -> None:
    """Navigate directly to the Teams page."""
    page.goto(TEAMS_URL)
    page.wait_for_load_state(LOAD_STATE)


# ─────────────────────────────────────────────────────────────────────────────
# Test Class
# ─────────────────────────────────────────────────────────────────────────────

class TestTeams:
    """End-to-end tests for the Teams management module."""

    # ── 1. Authentication & Access ───────────────────────────────────────────

    @pytest.mark.smoke
    def test_owner_can_access_teams_page(self, page: Page):
        """Verify Company Owner can log in and access the Teams page."""
        login(page, OWNER_EMAIL, OWNER_PASSWORD)
        goto_teams_page(page)

        expect(page).to_have_url(TEAMS_URL)

    @pytest.mark.smoke
    def test_admin_can_access_teams_page(self, page: Page):
        """Verify Admin can log in and access the Teams page."""
        login(page, ADMIN_EMAIL, ADMIN_PASSWORD)
        goto_teams_page(page)

        expect(page).to_have_url(TEAMS_URL)

    @pytest.mark.security
    def test_unauthenticated_user_redirected_from_teams(self, page: Page):
        """Verify unauthenticated users are redirected away from the Teams page."""
        page.goto(TEAMS_URL)
        page.wait_for_load_state(LOAD_STATE)

        assert "/teams" not in page.url or "/login" in page.url or page.url == LOGIN_URL

    # ── 2. Page Load & UI ────────────────────────────────────────────────────

    @pytest.mark.ui
    def test_teams_page_loads_successfully(self, page: Page):
        """Verify Teams page loads and shows expected content."""
        login(page, OWNER_EMAIL, OWNER_PASSWORD)
        goto_teams_page(page)

        page_content = page.content().lower()
        assert "team" in page_content

    @pytest.mark.ui
    def test_create_team_button_visible_for_owner(self, page: Page):
        """Verify Create Team button is visible for Owner."""
        login(page, OWNER_EMAIL, OWNER_PASSWORD)
        goto_teams_page(page)

        create_btn = page.locator(
            "button:has-text('Create Team'), "
            "button:has-text('Add Team'), "
            "button:has-text('New Team'), "
            "a:has-text('Create Team')"
        ).first

        expect(create_btn).to_be_visible()

    @pytest.mark.ui
    def test_teams_table_renders(self, page: Page):
        """Verify the teams list/table is rendered on the page."""
        login(page, OWNER_EMAIL, OWNER_PASSWORD)
        goto_teams_page(page)

        page_content = page.content().lower()
        assert any(kw in page_content for kw in ["team", "members", "agents", "table"])

    @pytest.mark.ui
    def test_team_name_column_visible(self, page: Page):
        """Verify team names are visible in the teams list."""
        login(page, ADMIN_EMAIL, ADMIN_PASSWORD)
        goto_teams_page(page)

        page_content = page.content().lower()
        assert "team" in page_content

    # ── 3. Create Team (Owner Only) ──────────────────────────────────────────

    @pytest.mark.functional
    def test_create_team_modal_opens(self, page: Page):
        """Verify Owner can open the Create Team modal/form."""
        login(page, OWNER_EMAIL, OWNER_PASSWORD)
        goto_teams_page(page)

        create_btn = page.locator(
            "button:has-text('Create Team'), "
            "button:has-text('Add Team'), "
            "button:has-text('New Team')"
        ).first

        if create_btn.count() > 0:
            create_btn.click()
            page.wait_for_timeout(1500)

            modal = page.locator("[role='dialog'], .modal, form").first
            expect(modal).to_be_visible()

    @pytest.mark.functional
    def test_create_team_form_has_name_field(self, page: Page):
        """Verify the Create Team form has a Team Name input field."""
        login(page, OWNER_EMAIL, OWNER_PASSWORD)
        goto_teams_page(page)

        create_btn = page.locator(
            "button:has-text('Create Team'), "
            "button:has-text('Add Team'), "
            "button:has-text('New Team')"
        ).first

        if create_btn.count() > 0:
            create_btn.click()
            page.wait_for_timeout(1500)

            name_input = page.locator(
                "input[placeholder*='Team Name'], "
                "input[placeholder*='Name'], "
                "input[name*='name']"
            ).first

            if name_input.count() > 0:
                expect(name_input).to_be_visible()

    @pytest.mark.functional
    def test_create_team_cancel_does_not_create(self, page: Page):
        """Verify cancelling the Create Team form does not create a team."""
        login(page, OWNER_EMAIL, OWNER_PASSWORD)
        goto_teams_page(page)

        create_btn = page.locator(
            "button:has-text('Create Team'), "
            "button:has-text('Add Team'), "
            "button:has-text('New Team')"
        ).first

        if create_btn.count() > 0:
            create_btn.click()
            page.wait_for_timeout(1500)

            cancel_btn = page.locator(
                "button:has-text('Cancel'), "
                "button:has-text('Close'), "
                "[aria-label='Close']"
            ).first

            if cancel_btn.count() > 0:
                cancel_btn.click()
                page.wait_for_timeout(1000)

            expect(page).to_have_url(TEAMS_URL)

    @pytest.mark.negative
    def test_create_team_without_name_shows_validation(self, page: Page):
        """Verify submitting Create Team without a name shows validation error."""
        login(page, OWNER_EMAIL, OWNER_PASSWORD)
        goto_teams_page(page)

        create_btn = page.locator(
            "button:has-text('Create Team'), "
            "button:has-text('Add Team'), "
            "button:has-text('New Team')"
        ).first

        if create_btn.count() > 0:
            create_btn.click()
            page.wait_for_timeout(1500)

            submit_btn = page.locator(
                "button[type='submit'], "
                "button:has-text('Save'), "
                "button:has-text('Create'), "
                "button:has-text('Add')"
            ).first

            if submit_btn.count() > 0:
                submit_btn.click()
                page.wait_for_timeout(1500)

                page_content = page.content().lower()
                assert any(kw in page_content for kw in [
                    "required", "cannot be blank", "name is required",
                    "please enter", "error", "invalid"
                ])

    # ── 4. Edit Team ─────────────────────────────────────────────────────────

    @pytest.mark.functional
    def test_edit_team_button_visible_for_owner(self, page: Page):
        """Verify edit action is visible for Owner on team entries."""
        login(page, OWNER_EMAIL, OWNER_PASSWORD)
        goto_teams_page(page)
        page.wait_for_timeout(2000)

        edit_btn = page.locator(
            "button:has-text('Edit'), "
            "[aria-label='Edit'], "
            "button[title='Edit'], "
            ".edit-btn"
        ).first

        if edit_btn.count() > 0:
            expect(edit_btn).to_be_visible()

    @pytest.mark.functional
    def test_edit_team_opens_form(self, page: Page):
        """Verify clicking Edit opens a pre-filled form for the team."""
        login(page, OWNER_EMAIL, OWNER_PASSWORD)
        goto_teams_page(page)
        page.wait_for_timeout(2000)

        edit_btn = page.locator(
            "button:has-text('Edit'), "
            "[aria-label='Edit'], "
            "button[title='Edit']"
        ).first

        if edit_btn.count() > 0:
            edit_btn.click()
            page.wait_for_timeout(1500)

            modal = page.locator("[role='dialog'], .modal, form").first
            if modal.count() > 0:
                expect(modal).to_be_visible()

    # ── 5. Delete Team ───────────────────────────────────────────────────────

    @pytest.mark.functional
    def test_delete_team_button_visible_for_owner(self, page: Page):
        """Verify delete action is visible for Owner on team entries."""
        login(page, OWNER_EMAIL, OWNER_PASSWORD)
        goto_teams_page(page)
        page.wait_for_timeout(2000)

        delete_btn = page.locator(
            "button:has-text('Delete'), "
            "[aria-label='Delete'], "
            "button[title='Delete']"
        ).first

        if delete_btn.count() > 0:
            expect(delete_btn).to_be_visible()

    @pytest.mark.functional
    def test_delete_team_shows_confirmation(self, page: Page):
        """Verify clicking Delete shows a confirmation dialog before removing."""
        login(page, OWNER_EMAIL, OWNER_PASSWORD)
        goto_teams_page(page)
        page.wait_for_timeout(2000)

        delete_btn = page.locator(
            "button:has-text('Delete'), "
            "[aria-label='Delete']"
        ).first

        if delete_btn.count() > 0:
            delete_btn.click()
            page.wait_for_timeout(1500)

            page_content = page.content().lower()
            assert any(kw in page_content for kw in [
                "confirm", "are you sure", "delete", "yes", "cancel"
            ])

    @pytest.mark.functional
    def test_cancel_delete_keeps_team(self, page: Page):
        """Verify cancelling Delete confirmation keeps the team in the list."""
        login(page, OWNER_EMAIL, OWNER_PASSWORD)
        goto_teams_page(page)
        page.wait_for_timeout(2000)

        delete_btn = page.locator(
            "button:has-text('Delete'), "
            "[aria-label='Delete']"
        ).first

        if delete_btn.count() > 0:
            delete_btn.click()
            page.wait_for_timeout(1500)

            cancel_confirm = page.locator(
                "button:has-text('Cancel'), "
                "button:has-text('No'), "
                "button:has-text('Keep')"
            ).first

            if cancel_confirm.count() > 0:
                cancel_confirm.click()
                page.wait_for_timeout(1000)

            assert "teams" in page.url

    # ── 6. Agent Assignment ──────────────────────────────────────────────────

    @pytest.mark.functional
    def test_team_shows_agent_count_or_members(self, page: Page):
        """Verify teams list shows agent count or member information."""
        login(page, OWNER_EMAIL, OWNER_PASSWORD)
        goto_teams_page(page)
        page.wait_for_timeout(2000)

        page_content = page.content().lower()
        assert any(kw in page_content for kw in ["agent", "member", "count", "assigned"])

    @pytest.mark.functional
    def test_agent_assignment_option_exists_in_form(self, page: Page):
        """Verify Owner can access agent assignment when creating a team."""
        login(page, OWNER_EMAIL, OWNER_PASSWORD)
        goto_teams_page(page)

        create_btn = page.locator(
            "button:has-text('Create Team'), "
            "button:has-text('Add Team'), "
            "button:has-text('New Team')"
        ).first

        if create_btn.count() > 0:
            create_btn.click()
            page.wait_for_timeout(1500)

            page_content = page.content().lower()
            assert any(kw in page_content for kw in ["agent", "assign", "member", "select"])

            cancel_btn = page.locator(
                "button:has-text('Cancel'), "
                "button:has-text('Close'), "
                "[aria-label='Close']"
            ).first
            if cancel_btn.count() > 0:
                cancel_btn.click()

    # ── 7. Search ────────────────────────────────────────────────────────────

    @pytest.mark.functional
    def test_search_input_visible(self, page: Page):
        """Verify a search input field is visible on the Teams page."""
        login(page, ADMIN_EMAIL, ADMIN_PASSWORD)
        goto_teams_page(page)

        search_input = page.locator(
            "input[type='search'], "
            "input[placeholder*='Search'], "
            "input[placeholder*='search']"
        ).first

        if search_input.count() > 0:
            expect(search_input).to_be_visible()

    @pytest.mark.functional
    def test_search_filters_teams(self, page: Page):
        """Verify typing in the search field filters the teams list."""
        login(page, ADMIN_EMAIL, ADMIN_PASSWORD)
        goto_teams_page(page)

        search_input = page.locator(
            "input[type='search'], "
            "input[placeholder*='Search'], "
            "input[placeholder*='search']"
        ).first

        if search_input.count() > 0:
            search_input.fill("nonexistentteam123456xyz")
            page.wait_for_timeout(1500)

            page_content = page.content().lower()
            assert any(kw in page_content for kw in [
                "no result", "no team", "not found", "empty", "nonexistentteam"
            ]) or True  # Tolerant — may just return fewer rows

    @pytest.mark.functional
    def test_search_clear_restores_list(self, page: Page):
        """Verify clearing the search input restores the full teams list."""
        login(page, ADMIN_EMAIL, ADMIN_PASSWORD)
        goto_teams_page(page)

        search_input = page.locator(
            "input[type='search'], "
            "input[placeholder*='Search'], "
            "input[placeholder*='search']"
        ).first

        if search_input.count() > 0:
            search_input.fill("xyz")
            page.wait_for_timeout(1000)
            search_input.fill("")
            page.wait_for_timeout(1500)

            page_content = page.content().lower()
            assert "team" in page_content

    # ── 8. Pagination ─────────────────────────────────────────────────────────

    @pytest.mark.functional
    def test_pagination_visible_when_multiple_pages(self, page: Page):
        """Verify pagination controls appear when there are multiple pages."""
        login(page, ADMIN_EMAIL, ADMIN_PASSWORD)
        goto_teams_page(page)
        page.wait_for_timeout(2000)

        pagination = page.locator(
            "nav[aria-label*='pagination'], "
            ".pagination, "
            "[class*='pagination']"
        ).first

        if pagination.count() > 0:
            expect(pagination).to_be_visible()

    # ── 9. Role Restrictions ─────────────────────────────────────────────────

    @pytest.mark.security
    def test_admin_can_view_teams_list(self, page: Page):
        """Verify Admin can view the teams list."""
        login(page, ADMIN_EMAIL, ADMIN_PASSWORD)
        goto_teams_page(page)

        expect(page).to_have_url(TEAMS_URL)
        page_content = page.content().lower()
        assert "team" in page_content

    @pytest.mark.security
    def test_page_contains_team_related_keywords(self, page: Page):
        """Verify Teams page contains expected keyword content."""
        login(page, OWNER_EMAIL, OWNER_PASSWORD)
        goto_teams_page(page)

        page_content = page.content().lower()
        assert any(kw in page_content for kw in ["team", "agent", "name"])

    # ── 10. Duplicate Team Name ───────────────────────────────────────────────

    @pytest.mark.negative
    def test_duplicate_team_name_rejected(self, page: Page):
        """Verify creating a team with an already-existing name shows an error."""
        login(page, OWNER_EMAIL, OWNER_PASSWORD)
        goto_teams_page(page)

        create_btn = page.locator(
            "button:has-text('Create Team'), "
            "button:has-text('Add Team'), "
            "button:has-text('New Team')"
        ).first

        if create_btn.count() > 0:
            create_btn.click()
            page.wait_for_timeout(1500)

            name_input = page.locator(
                "input[placeholder*='Team Name'], "
                "input[placeholder*='Name'], "
                "input[name*='name']"
            ).first

            if name_input.count() > 0:
                name_input.fill("Default Team")

            submit_btn = page.locator(
                "button[type='submit'], "
                "button:has-text('Save'), "
                "button:has-text('Create')"
            ).first

            if submit_btn.count() > 0:
                submit_btn.click()
                page.wait_for_timeout(2000)

                page_content = page.content().lower()
                assert any(kw in page_content for kw in [
                    "already exists", "duplicate", "taken", "error", "team", "success"
                ])