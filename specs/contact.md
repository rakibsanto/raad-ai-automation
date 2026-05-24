# Contact Module Specification

## Module Name
Contact Management

## Base URL
https://dev.prowhats.com/en

## Login URL
https://dev.prowhats.com/en/login

## Dashboard URL
https://dev.prowhats.com/en/dashboard

## Contacts URL
https://dev.prowhats.com/en/contacts/contacts

---

# User Roles

- Company Owner
- Admin
- Agent

---


# Login & Navigation Flow

Before accessing the Contact Management module, users must complete the login process.

## Expected Login Flow

1. Navigate to:
   https://dev.prowhats.com/en

2. Enter valid login credentials based on the user role.

3. Click the Login button.

4. After successful login, the system should redirect the user to:
   https://dev.prowhats.com/en/dashboard

5. From the dashboard, navigate to:
   https://dev.prowhats.com/en/contacts/contacts

6. The contacts page should load successfully.

---

# 1. Access Control

## Authorized Users

The following users can access the contacts page:
- Company Owner
- Admin
- Agent (Role-based data restriction may apply)

## Unauthorized Users

Unauthorized users must not be able to access contact data.

### Expected Behavior

- Redirect unauthorized users to login page.
- Show access denied message if direct URL is accessed.
- Contact data must not be visible.
- Logged-in users should successfully access the contacts page.
- After login, users should first land on the dashboard page before navigating to contacts.

---

# 2. Contact List Table

The main contacts page should display a table containing all available contacts.

## Table Columns

- Name
- Phone Number
- Email
- Tags/Groups
- Status
- Actions (Edit, Delete, View)

## Expected Behavior

- Display all authorized contacts in a responsive table format.
- Action buttons must be fully functional.
- Table should remain responsive on desktop, tablet, and mobile devices.
- Table headers should align correctly.
- Empty state should appear if no contacts exist.

---

# 3. Add Contact

Users should be able to add new contacts to the system manually.

## Required Fields

- Name
- Phone Number (with Country Code)

## Optional Fields

- Email
- Tags
- Notes

## Expected Behavior

- "Add Contact" button opens a modal or new page.
- Validation for phone number format.
- Success message upon creation.
- Table updates with the new contact immediately.
- Duplicate contacts should show validation errors.
- Required field validation should appear for blank inputs.

---

# 4. Import / Export Contacts

Users should be able to bulk import and export contact data.

## Import

- Allowed formats: `.csv`, `.xlsx`
- Mapping interface to map file columns to database fields.
- Error reporting for invalid rows.

## Export

- Formats: `.csv`, `.xlsx`
- Export current view (filtered) or all contacts.

## Expected Behavior

- Valid CSV/XLSX files should import successfully.
- Invalid rows should display proper error messages.
- Unsupported file types should be rejected.
- Exported files should contain correct contact data.

---

# 5. Search and Filters

Users should be able to quickly find specific contacts.

## Search Capabilities

- Click on the name search field and enter a name that automatically searches the contact names.
- Click on the phone search field and enter a phone number that automatically searches the contact phone numbers.

## Filter Options

- Filter by Tags/Groups
- Filter by Status
- Filter by Date Added

## Expected Behavior

- Table updates dynamically as the user types or selects filters.
- Clear button resets all filters.
- Partial name search should work.
- Search should be case insensitive.
- Empty state should appear when no matches are found.

---

# 6. Edit and Delete Contact

## Edit Functionality

- Clicking 'Edit' allows modification of all fields.
- Save changes dynamically updates the list.

## Delete Functionality

- Clicking 'Delete' triggers a confirmation prompt.
- Soft delete or hard delete depending on application rules.
- Table updates upon successful deletion.

## Expected Behavior

- Edit form should preload existing contact data.
- Updated data should reflect immediately after save.
- Delete confirmation modal should appear before deletion.
- Canceling delete action should keep the contact unchanged.

---

# 7. Pagination Rules

Pagination visibility depends on the total row count.

## Condition 1: Data ≤ 10

### Expected Behavior

- Pagination should be hidden or disabled.

---

## Condition 2: Data > 10

### Expected Behavior

- Pagination should be visible and functional.

## Pagination Functionalities

- Next Page
- Previous Page
- Page Number Selection
- Rows per page dropdown (10, 25, 50, 100)

## Expected Behavior

- Changing pages updates the table data correctly.
- Rows-per-page selector updates visible row count.
- Pagination controls remain responsive on mobile devices.

---

# 8. Error Handling

## Expected Behavior

- Show validation errors for incorrect phone formats or duplicate entries.
- Show a user-friendly error message if the API fails to load data.
- Handle network timeouts gracefully without breaking UI.
- Unauthorized API responses should redirect users to login.
- File import errors should display clear validation details.

---

# 9. Acceptance Criteria

The feature is complete when:

- Contacts list renders correctly with data from the backend.
- Authorized users can successfully log in.
- Successful login redirects users to dashboard.
- Users can navigate to the contacts page successfully.
- Adding a new contact works and updates the list.
- Search and filters correctly refine the list of contacts.
- Editing and deleting work correctly with proper confirmations.
- Import/Export functionality accurately processes `.csv`/`.xlsx` files.
- Pagination works correctly based on row count.
- Unauthorized access is blocked.
- Error handling works correctly across all major flows.

---

# 10. Detailed Test Scenarios

---

# 10.1 Authentication & Authorization

## Positive Test Cases

- Verify Company Owner can log in successfully.
- Verify Admin can log in successfully.
- Verify successful login redirects to dashboard.
- Verify authorized users can access contacts page.

## Negative Test Cases

- Verify unauthenticated users are redirected to login.
- Verify unauthorized users cannot access contact data directly.

---

# 10.2 Contact List View

## Positive Test Cases

- Verify the list renders correctly with data from the API.
- Verify column headers are correct.
- Verify table remains responsive on mobile/tablet devices.

## Negative Test Cases

- API failure shows empty state or error message.
- Empty state appears when no contacts exist.

---

# 10.3 Add Contact

## Positive Test Cases

- Create contact with all valid data.
- Create contact with only required fields.
- Verify newly added contact appears in the table immediately.

## Negative Test Cases

- Leave required fields blank.
- Enter invalid phone number format.
- Attempt to create a duplicate contact.

---

# 10.4 Search and Filter

## Positive Test Cases

- Search by exact name.
- Search by partial name.
- Search by phone number.
- Apply a tag filter and verify results.
- Apply status filter and verify results.
- Clear filters and verify original list is restored.

## Negative Test Cases

- Search string with no matches displays "No results found".

---

# 10.5 Edit & Delete

## Positive Test Cases

- Successfully update a contact's phone number.
- Successfully update optional fields.
- Successfully delete a contact after confirming the prompt.

## Negative Test Cases

- Cancel a delete action and ensure the contact remains.

---

# 10.6 Import/Export

## Positive Test Cases

- Import a valid CSV with 10 contacts.
- Import a valid XLSX file successfully.
- Export current list and verify file contents.

## Negative Test Cases

- Import CSV with invalid phone formats.
- Upload an unsupported file type (.pdf).
- Verify invalid rows display proper error messages.

---

# 10.7 Pagination

## Positive Test Cases

- Navigate to the next page and verify data updates.
- Navigate to the previous page and verify data updates.
- Change rows per page and verify row count.
- Select page number directly and verify table updates.

## Negative Test Cases

- Verify pagination is hidden when total rows are 10 or fewer.