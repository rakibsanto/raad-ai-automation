# Blocked Contact Module Specification

## Module Name
Blocked Contact Management

## Base URL
https://dev.prowhats.com/en

## Login URL
https://dev.prowhats.com/en/login

## Dashboard URL
https://dev.prowhats.com/en/dashboard

## Blocked Contacts URL
https://dev.prowhats.com/en/contacts/blocked-contacts

---

# User Roles

- Company Owner
- Admin
- Agent


---

# Login & Navigation Flow

Before accessing the Blocked Contacts module, users must complete the login process.

## Expected Login Flow

1. Navigate to:
   https://dev.prowhats.com/en

2. Enter valid login credentials based on the user role.

3. Click the Login button.

4. After successful login, the system should redirect the user to:
   https://dev.prowhats.com/en/dashboard

5. From the dashboard, navigate to:
   https://dev.prowhats.com/en/contacts/blocked-contacts

6. The blocked contacts page should load successfully.

---

# 1. Access Control

## Authorized Users

The following users can view the blocked contacts page:
- Company Owner
- Admin
- Agent

## Unauthorized Users

Without login, no one can visit this page.

### Expected Behavior

- Redirect unauthorized users to the login page if they try to access the URL directly.
- The blocked contacts list and actions must be completely hidden.
- Logged-in authorized users should successfully access the page.
- After login, users should first land on the dashboard page before navigating to blocked contacts.

---

# 2. Blocked Contact List

The main blocked contacts page should display a list/table of all blocked contacts.

## Expected Behavior

- Display all blocked contacts in a responsive list/table format.
- Ensure the list renders correctly populated with data from the API.
- Table/list should remain usable on desktop, tablet, and mobile devices.
- Data columns should align properly.
- Empty state should be shown if no blocked contacts exist.

---

# 3. Actions (Block/Unblock)

Users must be able to manage the block status for both campaigns and individual contacts.

## Expected Behavior

- A user can block a contact.
- A user can unblock a contact.
- A user can block a campaign.
- A user can unblock a campaign.
- UI should immediately reflect these changes.
- Updated status should appear without requiring manual refresh.
- Success/error toast or notification should appear after actions.
- System should prevent duplicate requests from multiple rapid clicks.

---

# 4. Search Functionality

Users must be able to search the blocked list to quickly find a specific entry.

## Expected Behavior

- Users can search by customer name.
- Search should dynamically filter the list/table.
- Search should work with partial names.
- Search should be case insensitive.
- Search should handle leading/trailing spaces properly.
- If no results are found, a "No results found" or similar empty state message is shown.
- Clearing the search field should restore the full list.

---

# 5. UI & Responsiveness

## Expected Behavior

- The blocked contacts page should be fully responsive.
- Table/list should not overflow outside the screen.
- Buttons and search fields should remain clickable on smaller screens.
- Text should remain readable on mobile devices.
- No overlapping UI components should appear.

---

# 6. Validation & Error Handling

## Expected Behavior

- System should handle API failures gracefully.
- Proper error message should appear if blocked contacts fail to load.
- Search should not crash with special characters.
- UI should remain stable during slow network responses.
- Unauthorized API responses should redirect users to login.

---

# 7. Acceptance Criteria

The feature is complete when:

- Unauthenticated access redirects to the login page.
- Company Owner, Admin, and Agent can successfully log in.
- Successful login redirects users to the dashboard page.
- Authorized users can navigate to and view the blocked contacts page.
- All blocked contacts are displayed in a list/table.
- Users can search for a blocked contact by customer name.
- Users can block and unblock campaigns and contacts successfully.
- UI updates immediately after actions.
- Empty states and error states display correctly.
- The page works properly on desktop and mobile devices.

---

# 8. Detailed Test Scenarios

## 8.1 Authentication & Authorization

- Verify unauthenticated users are redirected to login.
- Verify Company Owner can log in successfully.
- Verify Admin can log in successfully.
- Verify successful login redirects users to dashboard.
- Verify Company Owner, Admin, and Agent can access the blocked contacts page.
- Verify unauthorized users cannot access the page directly.

---

## 8.2 Navigation

- Verify users can navigate from dashboard to blocked contacts page.
- Verify direct URL access works after successful login.
- Verify browser refresh does not break the page.

---

## 8.3 View Blocked Contacts

- Verify the blocked contacts list renders correctly.
- Verify blocked contact data is displayed properly.
- Verify table headers are visible.
- Verify empty state is shown when no data exists.
- Verify API-loaded data appears correctly.

---

## 8.4 Block & Unblock Actions

- Verify the presence of "Block" action.
- Verify the presence of "Unblock" action.
- Verify users can block contacts successfully.
- Verify users can unblock contacts successfully.
- Verify users can block campaigns successfully.
- Verify users can unblock campaigns successfully.
- Verify UI updates immediately after actions.
- Verify success notification appears after action completion.
- Verify duplicate clicking does not create duplicate requests.

---

## 8.5 Search

- Verify search input field is visible.
- Verify searching by a valid customer name filters the list.
- Verify partial name search works.
- Verify search is case insensitive.
- Verify search trims unnecessary spaces.
- Verify searching for a non-existent name shows an appropriate empty state.
- Verify clearing search restores the original list.
- Verify special characters in search do not crash the UI.

---

## 8.6 Responsive Testing

- Verify page layout on desktop resolution.
- Verify page layout on tablet resolution.
- Verify page layout on mobile resolution.
- Verify buttons remain clickable on mobile devices.
- Verify no overlapping UI components appear.

---

## 8.7 Error Handling

- Verify proper error handling during API failure.
- Verify unauthorized API response redirects to login.
- Verify UI remains stable during slow loading conditions.
- Verify user-friendly error messages appear when necessary.