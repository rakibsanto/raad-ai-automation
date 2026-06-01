# Team Module Specification

## Module Name
Team Management

## URL
`$BASE_URL/teams` — resolved from `BASE_URL` in `.env`

## User Roles
- Company Owner
- Admin

---

# 1. Access Control

## Authorized Users
The following users can access the Teams page:
- Company Owner (full access: create, edit, delete, assign agents)
- Admin (read and limited access: view teams, manage members)

## Unauthorized Users
- Agent
- Unauthenticated users

### Expected Behavior
- Unauthenticated users attempting to access the Teams page must be redirected to the login page.
- Agents attempting to access this page should be denied (redirected or shown an error).
- Only Company Owner and Admin can successfully load and interact with the page.

---

# 2. Authentication & Access Flow

## Credentials

All credentials and URLs are loaded from the project's `.env` file. Do **not** hardcode credentials in test files.

| Variable         | Description                          |
|:---------------- |:-------------------------------------|
| `BASE_URL`       | Base URL of the application          |
| `LOGIN_URL`      | Login page URL                       |
| `DASHBOARD_URL`  | Dashboard URL after login            |
| `OWNER_EMAIL`    | Company Owner email                  |
| `OWNER_PASSWORD` | Company Owner password               |
| `ADMIN_EMAIL`    | Admin email                          |
| `ADMIN_PASSWORD` | Admin password                       |
| `AGENT_EMAIL`    | Agent email (for negative tests)     |
| `AGENT_PASSWORD` | Agent password (for negative tests)  |

## Authentication Flow
1. Navigate to `$LOGIN_URL` (from `.env`).
2. Enter `$OWNER_EMAIL` / `$OWNER_PASSWORD` or `$ADMIN_EMAIL` / `$ADMIN_PASSWORD` as required.
3. Click the **Login** button.
4. Upon successful login, the user is redirected to `$DASHBOARD_URL`.
5. Navigate to `$BASE_URL/teams`.

---

# 3. Role-Based Access Control (RBAC)

| Role          | Access Level       | Permissions                                                              |
|:------------- |:------------------ |:-------------------------------------------------------------------------|
| **Owner**     | **Full Access**    | View teams, create new teams, edit team name/description, delete teams, assign and remove agents from teams. |
| **Admin**     | **Limited Access** | View teams list and team members. May assign/remove agents depending on configuration. Cannot create or delete teams. |
| **Agent**     | **No Access**      | Blocked from accessing the page entirely.                                |

---

# 4. Team Management (CRUD)

## 4.1 Create Team (Owner Only)
The Owner can create a new team by clicking the **Create Team** button.

**Create Team Form Fields:**

| Field            | Type       | Required | Notes                                  |
|:---------------- |:---------- |:-------- |:-------------------------------------- |
| Team Name        | Text Input | Yes      | Must be unique; duplicate names rejected |
| Description      | Text Area  | No       | Brief description of the team's purpose |
| Assign Agents    | Multi-select / Dropdown | No | Select one or more agents to assign to this team |

**Expected Behavior:**
- Submitting the form with a valid, unique team name creates the team and it appears in the list.
- Submitting a duplicate team name must show an appropriate error message (e.g., "Team name already exists").
- Submitting without a required field (Team Name) shows a validation error.
- Cancelling or closing the modal discards changes and returns to the team list.

## 4.2 Edit Team (Owner Only)
The Owner can edit an existing team's details (name, description, members).

**Expected Behavior:**
- Clicking the edit button/icon for a team opens an edit form pre-filled with current values.
- Updating the team name to a name that already exists must be rejected.
- Saving valid changes updates the team details in the list.

## 4.3 Delete Team (Owner Only)
The Owner can delete a team from the system.

**Expected Behavior:**
- Clicking the delete action for a team shows a confirmation prompt.
- Confirming deletion removes the team from the list.
- Cancelling the confirmation keeps the team intact.

## 4.4 Duplicate Prevention
- The system must reject creating or renaming a team with a name that already exists.
- An appropriate error message should be displayed.

---

# 5. Agent Assignment

## 5.1 Assign Agents to a Team
- Authorized users (Owner, Admin) can assign one or more agents to a team.
- Assigning an agent means they can be linked to conversations routed to that team.

## 5.2 Remove Agents from a Team
- Authorized users can remove an agent from a team.
- Removing an agent does not delete the agent from the system — only from the team.

---

# 6. Table View & Features

## 6.1 Data Display
The teams list table shows all existing teams with the following columns:

| Column         | Description                                       |
|:-------------- |:------------------------------------------------- |
| Team Name      | The name of the team                              |
| Description    | Brief description of the team                     |
| Members / Agents Count | Number of agents assigned to the team     |
| Actions        | Edit and Delete buttons (Owner only)              |

## 6.2 Search
- Users can search the teams table by **Team Name**.
- The table updates dynamically as the user types.

## 6.3 Pagination
- The table includes pagination to navigate large lists of teams.
- The current page and total entries are visible.

---

# 7. Acceptance Criteria

The feature is considered complete when:

- [ ] Unauthenticated access redirects to the login page.
- [ ] Agents cannot access the Teams page.
- [ ] Owner and Admin can view the full list of teams.
- [ ] Owner can create a new team with a unique name.
- [ ] Duplicate team names are rejected with a descriptive error message.
- [ ] Owner can edit team name, description, and agent assignments.
- [ ] Owner can delete a team after confirming the action.
- [ ] Agents can be assigned to and removed from teams.
- [ ] The table displays team name, description, and agent count.
- [ ] Search by team name filters results dynamically.
- [ ] Pagination navigates between pages correctly.

---

# 8. Detailed Test Scenarios

## 8.1 Authentication & Authorization
- Verify Owner can log in and access the Teams page.
- Verify Admin can log in and access the Teams page.
- Verify unauthenticated users are redirected to the login page when trying to access `/teams`.
- Verify an Agent cannot access the Teams page.

## 8.2 Page Load & UI
- Verify the Teams page loads at `https://dev.prowhats.com/en/teams`.
- Verify the **Create Team** button is visible for the Owner.
- Verify the teams table/list is rendered on the page.
- Verify team entries display team name and agent count.

## 8.3 Create Team
- Verify the Owner can open the Create Team modal/form.
- Verify the form contains Team Name, Description, and Agent assignment fields.
- Verify creating a team with a valid unique name is successful.
- Verify creating a team without a name shows a validation error.
- Verify creating a team with a duplicate name is rejected with an error.
- Verify cancelling the form does not create a team.

## 8.4 Edit Team
- Verify the Owner can open the Edit Team form for an existing team.
- Verify the form is pre-filled with current team data.
- Verify saving valid changes updates the team name/description.
- Verify renaming to an existing team name is rejected.

## 8.5 Delete Team
- Verify the Owner can trigger the delete action.
- Verify a confirmation dialog/prompt appears before deletion.
- Verify confirming deletion removes the team from the list.
- Verify cancelling deletion keeps the team in the list.

## 8.6 Agent Assignment
- Verify the Owner can assign agents to a team.
- Verify the Owner can remove an agent from a team.
- Verify the agent count in the table updates after assignment/removal.

## 8.7 Search & Filter
- Verify searching for a team by name returns matching results.
- Verify searching for a non-existent name shows an empty/no-results state.
- Verify clearing the search restores the full team list.

## 8.8 Pagination
- Verify pagination controls are visible when more teams exist than can fit on one page.
- Verify clicking the next page shows the next set of teams.
