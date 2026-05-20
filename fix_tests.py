import re

file_path = "tests/test_qa_comprehensive.py"
with open(file_path, "r") as f:
    content = f.read()

# Replace input[type="tel"] with input[type="email"]
content = content.replace('input[type="tel"]', 'input[type="email"]')

# Refactor country search test to test password field
content = content.replace('test_qa03_xss_in_country_search', 'test_qa03_xss_in_password_field')
content = content.replace('XSS payload in country search field must not execute.', 'XSS payload in password field must not execute.')

# Replace the country search steps with password input steps
old_country_search = """        cc_btn = page.locator('[aria-label="Country code"]').first
        cc_btn.click()
        page.wait_for_selector('[placeholder="Search..."]', state="visible", timeout=5000)
        page.locator('[placeholder="Search..."]').fill(payload)
        page.wait_for_timeout(800)"""

new_password_search = """        pwd_input = page.locator('input[type="password"]').first
        pwd_input.fill(payload)
        page.wait_for_timeout(800)"""

content = content.replace(old_country_search, new_password_search)

# Replace the specific test string
content = content.replace('XSS in country search triggered alert:', 'XSS in password triggered alert:')

# Also fix the template injection test string
content = content.replace('test_qa03_template_injection_in_phone', 'test_qa03_template_injection_in_email')

# Also fix sqli test
content = content.replace('test_qa03_sqli_in_phone_field', 'test_qa03_sqli_in_email_field')
content = content.replace('SQL injection in phone field must not expose DB errors.', 'SQL injection in email field must not expose DB errors.')
content = content.replace('SQL injection leaked DB error', 'SQL injection leaked DB error')
content = content.replace('test_qa03_xss_in_phone_field', 'test_qa03_xss_in_email_field')

with open(file_path, "w") as f:
    f.write(content)

print("test_qa_comprehensive.py updated successfully!")
