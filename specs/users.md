# Users Module Documentation

This document outlines the user management workflow, permissions, and features for the Users tab within the Prowhats platform.

---

## 1. Authentication & Access

### Credentials
To access the system, use one of the following credentials depending on the test environment role:

* **Company Owner:**
    * **Email:** `saidurdev@gmail.com`
    * **Password:** `saidurdev@gmail.com`
* **Admin:**
    * **Email:** `rakibsanto1998@gmail.com`
    * **Password:** `111111`

### Authentication Flow
1. Navigate to the login page: `https://dev.prowhats.com/en`
2. Enter the appropriate credentials.
3. Upon successful login, users are automatically redirected to the Dashboard: `https://dev.prowhats.com/en/dashboard`
4. Navigate to the Users management page: `https://dev.prowhats.com/en/users`

---

## 2. Role-Based Access Control (RBAC)

The `https://dev.prowhats.com/en/users` page behaves differently depending on the logged-in user's role:

| Role | Access Level | Description & Permissions |
| :--- | :--- | :--- |
| **Owner** | **Full Access** | Can view all users, add new users, edit existing user details, delete users, and toggle user availability. |
| **Admin** | **Read-Only** | Can view the list of all company users (Owners, Admins, and Agents) but cannot create, edit, or delete data. |
| **Agent** | **No Access** | Restricted from viewing this page entirely. Agents should be blocked or redirected if trying to access the URL. |

---

## 3. Key Features & Functionalities

### User Management (Owner Only)
* **Create User:** The Owner can add new Admins or Agents by providing the following details:
    * Email
    * Phone Number
    * Password
    * Role Access (Admin / Agent)
* **Edit User:** The Owner can modify user details, including updating their role.
* **Delete User:** The Owner can remove a user from the company list.
* **Availability Toggle:** The Owner can instantly update a user's availability status using a toggle button directly inside the table row.

### Data Table Controls
* **Search:** Users can search the table dynamically by **User Name** or **Gmail/Email**.
* **Filtering:** Data can be filtered based on **User Type / Role** (Owner, Admin, Agent).
* **Pagination:** The table includes pagination to handle large lists of users efficiently.

---

## 4. System Email Notifications

The system automatically triggers email notifications during key lifecycle events:

> 🔔 **New User Creation:** When the Owner successfully adds a new user, the system automatically sends a welcome/notification email to the newly created Admin or Agent.
>
> 🔔 **Role Update:** If the Owner updates the role or permissions of any existing user, an automated email notification is immediately sent to that specific user informing them of the change.