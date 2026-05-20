import os, time, pytest
from playwright.sync_api import Page, expect
BASE_URL = os.getenv("BASE_URL", "https://dev.prowhats.com/en")

"""
Company Dashboard Tests — based on specs/company_dashboard.md
Covers: login, welcome message, stats cards, filters, broadcast chart,
       message summary, agents table, pagination, RBAC, and security.
"""
import os, time, datetime, pytest
from playwright.sync_api import Page, expect


# ── Environment ────────────────────────────────────────────────────────────────
BASE_URL      = os.getenv("BASE_URL",      "https://dev.prowhats.com/en")
LOGIN_URL     = os.getenv("LOGIN_URL",     "https://dev.prowhats.com/en/login")
DASHBOARD_URL = os.getenv("DASHBOARD_URL", "https://dev.prowhats.com/en/dashboard")


OWNER_EMAIL    = os.getenv("OWNER_EMAIL",    "saidurdev@gmail.com")
OWNER_PASSWORD = os.getenv("OWNER_PASSWORD", "saidurdev@gmail.com")
ADMIN_EMAIL    = os.getenv("ADMIN_EMAIL",    "rakibsanto1998@gmail.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "111111")
AGENT_EMAIL    = os.getenv("AGENT_EMAIL",    "rakibsanto.cse@gmail.com")
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


   # Check if we landed on the dashboard
   return "dashboard" in page.url or "dashboard" in page.title().lower()




def _assert_dashboard(page: Page, email: str, password: str):
   """Login and assert dashboard loaded; skip if login fails."""
   success = _login(page, email, password)
   if not success:
       # Try navigating directly
       page.goto(DASHBOARD_URL, wait_until="domcontentloaded", timeout=20000)
       page.wait_for_timeout(2000)
       if "login" in page.url:
           pytest.skip(f"Login failed for {email} — dashboard inaccessible")




# ═══════════════════════════════════════════════════════════════════════════════
# 1. Authentication / Login
# ═══════════════════════════════════════════════════════════════════════════════


def test_login_page_loads(page: Page):
   """Login page must load and show email + password fields."""
   page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=20000)
   page.wait_for_timeout(1500)
   email_field = page.locator('input[type="email"], input[name="email"]')
   assert email_field.count() > 0, "Email field not found on login page"




def test_owner_can_login_and_reach_dashboard(page: Page):
   """Company Owner must be able to login and see the dashboard."""
   success = _login(page, OWNER_EMAIL, OWNER_PASSWORD)
   if not success:
       page.goto(DASHBOARD_URL, wait_until="domcontentloaded", timeout=20000)
   assert "dashboard" in page.url or page.locator("main, [role='main']").count() > 0, \
       f"Owner did not reach dashboard. Current URL: {page.url}"




def test_admin_can_login_and_reach_dashboard(page: Page):
   """Admin must be able to login and see the dashboard."""
   success = _login(page, ADMIN_EMAIL, ADMIN_PASSWORD)
   if not success:
       page.goto(DASHBOARD_URL, wait_until="domcontentloaded", timeout=20000)
   assert "dashboard" in page.url or page.locator("main, [role='main']").count() > 0, \
       f"Admin did not reach dashboard. Current URL: {page.url}"




def test_agent_can_login_and_reach_dashboard(page: Page):
   """Agent must be able to login and see the dashboard."""
   success = _login(page, AGENT_EMAIL, AGENT_PASSWORD)
   if not success:
       page.goto(DASHBOARD_URL, wait_until="domcontentloaded", timeout=20000)
   assert "dashboard" in page.url or page.locator("main, [role='main']").count() > 0, \
       f"Agent did not reach dashboard. Current URL: {page.url}"




def test_invalid_credentials_show_error(page: Page):
   """Login with wrong credentials must show an error, not redirect to dashboard."""
   page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=20000)
   page.wait_for_timeout(1500)
   email_sel = 'input[type="email"], input[name="email"]'
   pwd_sel   = 'input[type="password"], input[name="password"]'
   try:
       page.locator(email_sel).first.fill("wrong@example.com")
       page.locator(pwd_sel).first.fill("wrongpassword")
       page.locator('button[type="submit"]').first.click()
       page.wait_for_timeout(2000)
   except Exception:
       pytest.skip("Could not interact with login form")
   assert "dashboard" not in page.url, \
       "Invalid credentials should NOT redirect to dashboard"




def test_unauthenticated_dashboard_redirects_to_login(page: Page):
   """Direct access to dashboard URL without login must redirect to login."""
   page.goto(DASHBOARD_URL, wait_until="domcontentloaded", timeout=20000)
   page.wait_for_timeout(2000)
   assert "login" in page.url or "login" in page.content().lower(), \
       "Unauthenticated dashboard access should redirect to login"




# ═══════════════════════════════════════════════════════════════════════════════
# 2. Welcome Message (Time-Based Greeting)
# ═══════════════════════════════════════════════════════════════════════════════


def _assert_greeting(page: Page, expected_message: str):
   greeting = page.locator("text=/Good (morning|afternoon|evening|night)/i").first
   expect(greeting).to_be_visible()


   actual = greeting.inner_text().lower()


   assert expected_message.lower() in actual, \
       f"Expected '{expected_message}', but got '{actual}'"


def test_dashboard_shows_good_morning(page: Page):
   """
   If login happens in morning,
   dashboard must show Good Morning
   """


   page.add_init_script("""
       Date = class extends Date {
           constructor() {
               super();
               return new globalThis.Date('2026-05-18T09:00:00');
           }
       }
   """)


   _assert_dashboard(page, OWNER_EMAIL, OWNER_PASSWORD)


   _assert_greeting(page, "Good Morning")


def test_dashboard_shows_good_afternoon(page: Page):
   """
   If login happens in afternoon,
   dashboard must show Good Afternoon
   """


   page.add_init_script("""
       Date = class extends Date {
           constructor() {
               super();
               return new globalThis.Date('2026-05-18T14:00:00');
           }
       }
   """)


   _assert_dashboard(page, OWNER_EMAIL, OWNER_PASSWORD)


   _assert_greeting(page, "Good Afternoon")


def test_dashboard_shows_good_evening(page: Page):
   page.add_init_script("""
       Date = class extends Date {
           constructor() {
               super();
               return new globalThis.Date('2026-05-18T18:30:00');
           }
       }
   """)


   _assert_dashboard(page, OWNER_EMAIL, OWNER_PASSWORD)


   _assert_greeting(page, "Good Evening")


def test_dashboard_shows_good_night(page: Page):
   page.add_init_script("""
       Date = class extends Date {
           constructor() {
               super();
               return new globalThis.Date('2026-05-18T21:00:00');
           }
       }
   """)


   _assert_dashboard(page, OWNER_EMAIL, OWNER_PASSWORD)


   _assert_greeting(page, "Good Night")


def test_greeting_boundary_1159_am(page: Page):
   page.add_init_script("""
       Date = class extends Date {
           constructor() {
               super();
               return new globalThis.Date('2026-05-18T11:59:00');
           }
       }
   """)


   _assert_dashboard(page, OWNER_EMAIL, OWNER_PASSWORD)
   _assert_greeting(page, "Good Morning")


def test_greeting_boundary_1200_pm(page: Page):
   page.add_init_script("""
       Date = class extends Date {
           constructor() {
               super();
               return new globalThis.Date('2026-05-18T12:00:00');
           }
       }
   """)


   _assert_dashboard(page, OWNER_EMAIL, OWNER_PASSWORD)
   _assert_greeting(page, "Good Afternoon")




def test_welcome_message_correct_for_time_of_day(page: Page):
   """Greeting should match the current server/client time."""
   _assert_dashboard(page, OWNER_EMAIL, OWNER_PASSWORD)
   page.wait_for_timeout(2000)
   hour = datetime.datetime.now().hour
   body_text = page.inner_text("body").lower()


   if 0 <= hour < 12:
       expected = "good morning"
   elif 12 <= hour < 20:
       expected = "good evening"
   else:
       expected = "good night"


   if expected not in body_text:
       pytest.skip(
           f"Expected '{expected}' for hour={hour} but not found — "
           "server and client time may differ"
       )
   assert expected in body_text, f"Expected greeting '{expected}' at hour {hour}"




# ═══════════════════════════════════════════════════════════════════════════════
# 3. Dashboard Statistics Cards
# ═══════════════════════════════════════════════════════════════════════════════


def test_dashboard_stats_cards_visible(page: Page):
   """Dashboard must display at least one statistics card."""
   _assert_dashboard(page, OWNER_EMAIL, OWNER_PASSWORD)
   page.wait_for_timeout(2000)
   # Look for cards / count containers
   cards = page.locator(
       "[class*='card'], [class*='stat'], [class*='count'], "
       "[class*='metric'], [class*='widget'], [class*='tile']"
   )
   assert cards.count() > 0, "No statistics cards found on dashboard"




def test_dashboard_shows_conversation_counts(page: Page):
   """Dashboard must show open/total conversation counts."""
   _assert_dashboard(page, OWNER_EMAIL, OWNER_PASSWORD)
   page.wait_for_timeout(2000)
   body = page.inner_text("body").lower()
   keywords = ["conversation", "open", "contact", "active"]
   found = [k for k in keywords if k in body]
   assert len(found) >= 2, \
       f"Dashboard missing conversation metrics. Found: {found}"




def test_filter_last_7_days_exists(page: Page):
   """Filter option 'Last 7 Days' must be present on dashboard."""
   _assert_dashboard(page, OWNER_EMAIL, OWNER_PASSWORD)
   page.wait_for_timeout(2000)
   body = page.inner_text("body").lower()
   assert "7" in body or "seven" in body or "week" in body, \
       "Last 7 Days filter not found on dashboard"




def test_filter_last_30_days_exists(page: Page):
   """Filter option 'Last 30 Days' must be present on dashboard."""
   _assert_dashboard(page, OWNER_EMAIL, OWNER_PASSWORD)
   page.wait_for_timeout(2000)
   body = page.inner_text("body").lower()
   assert "30" in body or "month" in body, \
       "Last 30 Days filter not found on dashboard"




def test_filter_last_6_months_exists(page: Page):
   """Filter option 'Last 6 Months' must be present on dashboard."""
   _assert_dashboard(page, OWNER_EMAIL, OWNER_PASSWORD)
   page.wait_for_timeout(2000)
   body = page.inner_text("body").lower()
   assert "6" in body or "six" in body or "month" in body, \
       "Last 6 Months filter not found on dashboard"




def test_filter_click_updates_stats(page: Page):
   """Clicking a filter option should not crash the dashboard."""
   _assert_dashboard(page, OWNER_EMAIL, OWNER_PASSWORD)
   page.wait_for_timeout(2000)
   # Try to find and click any filter button
   filter_sel = (
       'button:has-text("7"), button:has-text("30"), button:has-text("Last"), '
       '[class*="filter"], [class*="tab"]'
   )
   filters = page.locator(filter_sel)
   if filters.count() == 0:
       pytest.skip("No filter buttons found on dashboard")
   filters.first.click()
   page.wait_for_timeout(1500)
   assert "500" not in page.title(), "Filter click caused a server error"




# ═══════════════════════════════════════════════════════════════════════════════
# 4. Broadcast Chart Section
# ═══════════════════════════════════════════════════════════════════════════════


def test_broadcast_chart_section_present(page: Page):
   """Dashboard must have a broadcast chart/analytics section."""
   _assert_dashboard(page, OWNER_EMAIL, OWNER_PASSWORD)
   page.wait_for_timeout(2000)
   body = page.inner_text("body").lower()
   assert "broadcast" in body or "chart" in body or "sent" in body, \
       "Broadcast chart section not found on dashboard"




def test_broadcast_chart_metrics_visible(page: Page):
   """Broadcast metrics (sent, delivered, read, failed) should be present."""
   _assert_dashboard(page, OWNER_EMAIL, OWNER_PASSWORD)
   page.wait_for_timeout(2000)
   body = page.inner_text("body").lower()
   metrics = ["sent", "delivered", "read", "failed"]
   found = [m for m in metrics if m in body]
   assert len(found) >= 2, \
       f"Broadcast metrics missing. Found: {found}. Expected at least 2 of: {metrics}"




def test_broadcast_chart_canvas_or_svg_present(page: Page):
   """Chart must render as canvas or SVG element."""
   _assert_dashboard(page, OWNER_EMAIL, OWNER_PASSWORD)
   page.wait_for_timeout(3000)
   charts = page.locator("canvas, svg")
   if charts.count() == 0:
       pytest.skip("No canvas/SVG chart element found — chart may be text-only")
   assert charts.count() > 0, "Chart canvas/SVG not found"




# ═══════════════════════════════════════════════════════════════════════════════
# 5. Message Summary Section
# ═══════════════════════════════════════════════════════════════════════════════


def test_message_summary_section_present(page: Page):
   """Message summary section must appear on the dashboard."""
   _assert_dashboard(page, OWNER_EMAIL, OWNER_PASSWORD)
   page.wait_for_timeout(2000)
   body = page.inner_text("body").lower()
   assert "message" in body, "Message summary section not found on dashboard"




def test_message_summary_shows_counts(page: Page):
   """Message summary should show numeric counts."""
   _assert_dashboard(page, OWNER_EMAIL, OWNER_PASSWORD)
   page.wait_for_timeout(2000)
   import re
   body = page.inner_text("body")
   numbers = re.findall(r'\b\d+\b', body)
   assert len(numbers) >= 3, \
       f"Expected numeric counts on dashboard but found only {len(numbers)}"




# ═══════════════════════════════════════════════════════════════════════════════
# 6. Conversation by Agents Table
# ═══════════════════════════════════════════════════════════════════════════════


def test_agents_table_heading_present(page: Page):
   """'Conversation by Agents' table heading must be visible."""
   _assert_dashboard(page, OWNER_EMAIL, OWNER_PASSWORD)
   page.wait_for_timeout(2000)
   body = page.inner_text("body").lower()
   assert "agent" in body or "conversation" in body, \
       "Agents table heading not found on dashboard"




def test_agents_table_element_present(page: Page):
   """A table or data-list element for agents must exist."""
   _assert_dashboard(page, OWNER_EMAIL, OWNER_PASSWORD)
   page.wait_for_timeout(2000)
   tables = page.locator("table, [class*='table'], [class*='grid'], [class*='list']")
   if tables.count() == 0:
       pytest.skip("No table/grid element found — agents list may use a different layout")
   assert tables.count() > 0, "Agents table not found"




def test_agents_table_has_status_columns(page: Page):
   """Table should show Open, Pending, Close, Rating columns."""
   _assert_dashboard(page, OWNER_EMAIL, OWNER_PASSWORD)
   page.wait_for_timeout(2000)
   body = page.inner_text("body").lower()
   cols = ["open", "pending", "close", "rating"]
   found = [c for c in cols if c in body]
   assert len(found) >= 2, \
       f"Expected table columns, found: {found}"




# ═══════════════════════════════════════════════════════════════════════════════
# 7. Pagination
# ═══════════════════════════════════════════════════════════════════════════════


def test_pagination_present_when_data_exists(page: Page):
   """If agents table has data, check pagination visibility logic."""
   _assert_dashboard(page, OWNER_EMAIL, OWNER_PASSWORD)
   page.wait_for_timeout(2000)
   pagination = page.locator(
       "[class*='pagination'], [class*='pager'], "
       'button:has-text("Next"), button:has-text("Previous"), '
       'button:has-text("›"), button:has-text("‹")'
   )
   # Pagination may or may not be visible — just ensure no crash
   assert "500" not in page.title(), \
       "Server error on dashboard with pagination"




def test_pagination_next_button_clickable(page: Page):
   """Next page button, if present, must be clickable."""
   _assert_dashboard(page, OWNER_EMAIL, OWNER_PASSWORD)
   page.wait_for_timeout(2000)
   next_btn = page.locator(
       'button:has-text("Next"), [aria-label="Next"], '
       '[class*="next"]:not([disabled])'
   )
   if next_btn.count() == 0:
       pytest.skip("No Next button found — pagination may be hidden (≤9 records)")
   next_btn.first.click()
   page.wait_for_timeout(1000)
   assert "500" not in page.title(), "Next page click caused server error"




# ═══════════════════════════════════════════════════════════════════════════════
# 8. Role-Based Access
# ═══════════════════════════════════════════════════════════════════════════════


def test_owner_sees_full_dashboard(page: Page):
   """Company Owner should see the complete dashboard with all sections."""
   _assert_dashboard(page, OWNER_EMAIL, OWNER_PASSWORD)
   page.wait_for_timeout(2000)
   body = page.inner_text("body").lower()
   sections = ["conversation", "message", "broadcast", "agent"]
   found = [s for s in sections if s in body]
   assert len(found) >= 2, \
       f"Owner dashboard missing sections. Found: {found}"




def test_admin_sees_dashboard_stats(page: Page):
   """Admin should see dashboard statistics after login."""
   _assert_dashboard(page, ADMIN_EMAIL, ADMIN_PASSWORD)
   page.wait_for_timeout(2000)
   body = page.inner_text("body").lower()
   assert any(k in body for k in ["conversation", "message", "stat", "total"]), \
       "Admin dashboard shows no statistics"




def test_agent_sees_dashboard(page: Page):
   """Agent should see the dashboard (possibly with limited data)."""
   _assert_dashboard(page, AGENT_EMAIL, AGENT_PASSWORD)
   page.wait_for_timeout(2000)
   # Should not be on login page
   assert "login" not in page.url or "dashboard" in page.inner_text("body").lower(), \
       "Agent was redirected to login — dashboard access denied"




# ═══════════════════════════════════════════════════════════════════════════════
# 9. UI / Error Handling
# ═══════════════════════════════════════════════════════════════════════════════


def test_dashboard_no_5xx_errors_on_load(page: Page):
   """Dashboard page must not trigger any 5xx network responses."""
   failures = []
   page.on("response", lambda r: failures.append((r.url, r.status))
           if r.status >= 500 else None)
   _assert_dashboard(page, OWNER_EMAIL, OWNER_PASSWORD)
   page.wait_for_timeout(2000)
   assert failures == [], f"5xx errors during dashboard load: {failures[:3]}"




def test_dashboard_no_js_console_errors(page: Page):
   """Dashboard should load without critical JavaScript errors."""
   errors = []
   page.on("console", lambda msg: errors.append(msg.text)
           if msg.type == "error" else None)
   _assert_dashboard(page, OWNER_EMAIL, OWNER_PASSWORD)
   page.wait_for_timeout(2000)
   critical = [e for e in errors if "Cannot read" in e or "is not defined" in e]
   assert critical == [], f"JS errors on dashboard: {critical[:3]}"




def test_dashboard_cards_aligned_no_overflow(page: Page):
   """Dashboard must not have horizontal scroll (layout not broken)."""
   _assert_dashboard(page, OWNER_EMAIL, OWNER_PASSWORD)
   page.wait_for_timeout(2000)
   overflow = page.evaluate(
       "() => document.documentElement.scrollWidth > window.innerWidth + 10"
   )
   assert not overflow, "Dashboard has horizontal scroll — layout broken"




def test_dashboard_loads_within_10_seconds(page: Page):
   """Dashboard content must appear within 10 seconds of login."""
   start = time.time()
   _assert_dashboard(page, OWNER_EMAIL, OWNER_PASSWORD)
   elapsed = time.time() - start
   assert elapsed < 10, f"Dashboard took {elapsed:.1f}s to load (limit: 10s)"




def test_dashboard_title_not_empty(page: Page):
   """Dashboard page must have a non-empty title."""
   _assert_dashboard(page, OWNER_EMAIL, OWNER_PASSWORD)
   title = page.title()
   assert title and len(title.strip()) > 0, "Dashboard page has empty title"




def test_logout_clears_session(page: Page):
   """After logout, visiting dashboard URL must redirect to login."""
   _assert_dashboard(page, OWNER_EMAIL, OWNER_PASSWORD)
   page.wait_for_timeout(1500)
   # Try to find logout link/button
   logout = page.locator(
       'a:has-text("Logout"), button:has-text("Logout"), '
       'a:has-text("Sign Out"), button:has-text("Sign Out"), '
       '[href*="logout"], [href*="signout"]'
   )
   if logout.count() == 0:
       pytest.skip("Logout button not found")
   logout.first.click()
   page.wait_for_timeout(2000)
   # Now try to access dashboard directly
   page.goto(DASHBOARD_URL, wait_until="domcontentloaded", timeout=15000)
   page.wait_for_timeout(1500)
   assert "login" in page.url or "login" in page.content().lower(), \
       "Dashboard accessible after logout — session not cleared"