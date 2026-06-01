import os, time, pytest
from playwright.sync_api import Page, expect
BASE_URL = os.getenv("BASE_URL", "https://dev.prowhats.com/en")

# test_users.py

import os
import time
import random
import string
import pytest
from playwright.sync_api import Page, expect
from dotenv import load_dotenv

# ─────────────────────────────────────────────────────────────
# Load Environment Variables
# ─────────────────────────────────────────────────────────────
load_dotenv()

BASE_URL = os.getenv("BASE_URL", "https://dev.prowhats.com/en")
LOGIN_URL = os.getenv("LOGIN_URL", "https://dev.prowhats.com/en/login")
DASHBOARD_URL = os.getenv("DASHBOARD_URL", "https://dev.prowhats.com/en/dashboard")
USERS_URL = os.getenv("USERS_URL", "https://dev.prowhats.com/en/users")

OWNER_EMAIL = os.getenv("OWNER_EMAIL")
OWNER_PASSWORD = os.getenv("OWNER_PASSWORD")

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

# ─────────────────────────────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────────────────────────────
def login(page: Page, email: str, password: str):
    page.goto(LOGIN_URL)

    page.fill('input[type="email"]', email)
    page.fill('input[type="password"]', password)

    page.click('button[type="submit"]')

    page.wait_for_url("**/dashboard", timeout=30000)
    expect(page).to_have_url(DASHBOARD_URL)


def goto_users_page(page: Page):
    page.goto(USERS_URL)
    page.wait_for_load_state("networkidle")


def generate_random_user():
    random_text = ''.join(random.choices(string.ascii_lowercase, k=5))

    return {
        "name": f"Test User {random_text}",
        "email": f"testuser_{random_text}@gmail.com",
        "phone": f"017{random.randint(10000000, 99999999)}",
        "password": "Test@12345"
    }


# ─────────────────────────────────────────────────────────────
# Test: Owner Login & Access Users Page
# ─────────────────────────────────────────────────────────────
def test_owner_can_access_users_page(page: Page):
    login(page, OWNER_EMAIL, OWNER_PASSWORD)

    goto_users_page(page)

    expect(page).to_have_url(USERS_URL)


# ─────────────────────────────────────────────────────────────
# Test: Admin Can Access Users Page (Read Only)
# ─────────────────────────────────────────────────────────────
def test_admin_can_view_users_page(page: Page):
    login(page, ADMIN_EMAIL, ADMIN_PASSWORD)

    goto_users_page(page)

    expect(page).to_have_url(USERS_URL)


# ─────────────────────────────────────────────────────────────
# Test: Agent Should Not Access Users Page
# ─────────────────────────────────────────────────────────────
@pytest.mark.skip(reason="Requires valid Agent credentials in .env")
def test_agent_should_not_access_users_page(page: Page):
    agent_email = os.getenv("AGENT_EMAIL")
    agent_password = os.getenv("AGENT_PASSWORD")

    login(page, agent_email, agent_password)

    page.goto(USERS_URL)

    time.sleep(2)

    assert (
        "/users" not in page.url
        or page.locator("text=Unauthorized").count() > 0
    )


# ─────────────────────────────────────────────────────────────
# Test: Owner Can Create New User
# ─────────────────────────────────────────────────────────────
def test_owner_can_create_new_user(page: Page):
    login(page, OWNER_EMAIL, OWNER_PASSWORD)

    goto_users_page(page)

    user = generate_random_user()

    # Click Add User Button
    page.click("text=Add User")

    # Fill User Form
    page.fill('input[name="name"]', user["name"])
    page.fill('input[name="email"]', user["email"])
    page.fill('input[name="phone"]', user["phone"])
    page.fill('input[name="password"]', user["password"])

    # Select Role
    page.select_option('select[name="role"]', "agent")

    # Submit Form
    page.click('button[type="submit"]')

    page.wait_for_load_state("networkidle")

    # Verify User Added
    expect(page.locator(f"text={user['email']}")).to_be_visible()


# ─────────────────────────────────────────────────────────────
# Test: Owner Can Search User By Email
# ─────────────────────────────────────────────────────────────
def test_search_user_by_email(page: Page):
    login(page, OWNER_EMAIL, OWNER_PASSWORD)

    goto_users_page(page)

    search_email = "rakibsanto1998@gmail.com"

    # Search Input
    page.fill('input[placeholder*="Search"]', search_email)

    page.wait_for_timeout(1500)

    expect(page.locator(f"text={search_email}")).to_be_visible()


# ─────────────────────────────────────────────────────────────
# Test: Filter Users By Role
# ─────────────────────────────────────────────────────────────
def test_filter_users_by_role(page: Page):
    login(page, OWNER_EMAIL, OWNER_PASSWORD)

    goto_users_page(page)

    # Select Agent Filter
    page.select_option('select', label="Agent")

    page.wait_for_timeout(2000)

    # Verify Filter Applied
    expect(page.locator("text=Agent").first).to_be_visible()


# ─────────────────────────────────────────────────────────────
# Test: Pagination Exists
# ─────────────────────────────────────────────────────────────
def test_users_table_pagination(page: Page):
    login(page, OWNER_EMAIL, OWNER_PASSWORD)

    goto_users_page(page)

    pagination = page.locator("nav[aria-label='pagination']")

    expect(pagination).to_be_visible()


# ─────────────────────────────────────────────────────────────
# Test: Owner Can Toggle User Availability
# ─────────────────────────────────────────────────────────────
def test_owner_can_toggle_user_availability(page: Page):
    login(page, OWNER_EMAIL, OWNER_PASSWORD)

    goto_users_page(page)

    toggle = page.locator('button[role="switch"]').first

    expect(toggle).to_be_visible()

    toggle.click()

    page.wait_for_timeout(1500)


# ─────────────────────────────────────────────────────────────
# Test: Admin Cannot Create User
# ─────────────────────────────────────────────────────────────
def test_admin_cannot_create_user(page: Page):
    login(page, ADMIN_EMAIL, ADMIN_PASSWORD)

    goto_users_page(page)

    add_user_button = page.locator("text=Add User")

    expect(add_user_button).not_to_be_visible()


# ─────────────────────────────────────────────────────────────
# Test: Owner Can Delete User
# ─────────────────────────────────────────────────────────────
def test_owner_can_delete_user(page: Page):
    login(page, OWNER_EMAIL, OWNER_PASSWORD)

    goto_users_page(page)

    delete_button = page.locator("button:has-text('Delete')").first

    if delete_button.count() > 0:
        delete_button.click()

        # Confirm Delete
        confirm_button = page.locator("button:has-text('Confirm')")

        if confirm_button.count() > 0:
            confirm_button.click()

        page.wait_for_load_state("networkidle")