# Manage Group Module Specification

## Module Name
Manage Group

## URL
https://dev.prowhats.com/en/contacts/manage-group

## User Roles
- Company Owner
- Admin

---

# 1. Access Control

## Authorized Users
The following users can view the manage group page:
- Company Owner
- Admin

## Unauthorized Users
- Agent
- Unauthenticated users

### Expected Behavior
- Redirect unauthenticated users to the login page.
- Agents attempting to access this page should be denied access (e.g., redirected or shown an error, page should not be visible).
- Only Company Owner and Admin can successfully load and interact with the page.

---

# 2. Group Management (CRUD)

## Expected Behavior
- **Create:** Authorized users can create a new group.
- **Update:** Authorized users can edit/update an existing group's details.
- **Delete:** Authorized users can delete a group.
- **Duplicate Prevention:** The system must prevent creating a new group with a name that already exists in the system. It should show an appropriate error message.

---

# 3. Customer Management within Groups

## Expected Behavior
- **Include/Remove:** Users can manually add or remove customers from any group.
- **Import:** Users can upload an Excel file to bulk import customers into a specific group.
- **Export:** Users can download the list of customers in a group as a CSV file.

---

# 4. Table View & Features

## Expected Behavior
- **Data Display:** The main table displays all groups.
- **Customer Count:** The table must explicitly show the number of customers currently in each group on the table.
- **Search:** Users can search the table data by group name. The table updates dynamically based on the input.
- **Pagination:** The table must support pagination to handle navigating through large lists of groups.

---

# 5. Acceptance Criteria

The feature is complete when:
- Unauthenticated access redirects to login.
- Agents cannot access the Manage Group page.
- Owners and Admins can view the page and perform all CRUD operations on groups.
- Duplicate group names are rejected during creation.
- Customers can be added, removed, imported via Excel, and exported via CSV for any group.
- The table displays the group name, customer count, supports searching by group name, and includes working pagination.

---

# 6. Detailed Test Scenarios

## 6.1 Authentication & Authorization
- Verify unauthenticated users are redirected to login.
- Verify Company Owner and Admin can access the page.
- Verify Agent cannot access the page.

## 6.2 Group CRUD Operations
- Verify creating a new group.
- Verify updating an existing group.
- Verify deleting a group.
- Verify creating a group with an existing name fails with an error.

## 6.3 Customer Management
- Verify including a customer in a group.
- Verify removing a customer from a group.
- Verify uploading an Excel file to import customers.
- Verify downloading a CSV file of the group's customers.

## 6.4 Table Functionality
- Verify the table displays the number of customers per group.
- Verify searching by group name filters the table correctly.
- Verify pagination controls navigate between pages correctly.
