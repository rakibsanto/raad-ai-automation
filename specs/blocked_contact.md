# Blocked Contact Module Specification

## Module Name
Blocked Contact Management

## URL
https://dev.prowhats.com/en/contacts/blocked-contacts

## User Roles
- Company Owner
- Admin
- Agent

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

---

# 2. Blocked Contact List

The main blocked contacts page should display a list/table of all blocked contacts.

## Expected Behavior
- Display all blocked contacts in a responsive list/table format.
- Ensure the list renders correctly populated with data from the API.

---

# 3. Actions (Block/Unblock)

Users must be able to manage the block status for both campaigns and individual contacts.

## Expected Behavior
- A user can block a contact or campaign.
- A user can unblock a contact or campaign.
- UI should immediately reflect these changes (e.g. status updates, list refreshes).

---

# 4. Search functionality

Users must be able to search the blocked list to quickly find a specific entry.

## Expected Behavior
- Users can search by customer name.
- The list/table updates dynamically as the user types or submits the search.
- If no results are found, a "No results found" or similar empty state message is shown.

---

# 5. Acceptance Criteria

The feature is complete when:
- Unauthenticated access redirects to the login page.
- Company Owner, Admin, and Agent can successfully navigate to and view the blocked contacts page.
- All blocked contacts are displayed in a list.
- Users can search for a blocked contact by customer name.
- Users can block and unblock for campaign and contact, and the system processes it without errors.

---

# 6. Detailed Test Scenarios

## 6.1 Authentication & Authorization
- Verify unauthenticated users are redirected to login.
- Verify Company Owner, Admin, and Agent can access the page.

## 6.2 View Blocked Contacts
- Verify the blocked contacts list renders correctly.

## 6.3 Block & Unblock Actions
- Verify the presence and functionality of "Block" and "Unblock" actions for campaign and contact.

## 6.4 Search
- Verify that searching by a valid customer name filters the list.
- Verify that searching for a non-existent name shows an appropriate empty state.
