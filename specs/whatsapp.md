
## 1. Module Overview
- **Module Name:** WhatsApp Chat
- **Description:** The WhatsApp Chat page allows Company Owner, Admin, and Agent users to manage, track, and reply to customer conversations from connected WhatsApp numbers.

---

## 2. System URLs & Access

### 2.1 Web Endpoints
| Page / Action | URL |
| :--- | :--- |
| **Base URL** | `https://dev.prowhats.com/en` |
| **Login URL** | `https://dev.prowhats.com/en/login` |
| **Dashboard URL** | `https://dev.prowhats.com/en/dashboard` |
| **WhatsApp Chat URL** | `https://dev.prowhats.com/en/contacts/whatsapp-chat` |

### 2.2 System Roles
- **Company Owner**
- **Admin**
- **Agent**

### 2.3 Pre-configured Login Credentials
- **Company Owner Credentials**
  - `OWNER_EMAIL=saidurdev@gmail.com`
  - `OWNER_PASSWORD=saidurdev@gmail.com`
- **Admin Credentials**
  - `ADMIN_EMAIL=rakibsanto1998@gmail.com`
  - `ADMIN_PASSWORD=111111`

---

## 3. Core Workflows

### 3.1 Login & Navigation Flow
1. Open the Base/Login URL: `https://dev.prowhats.com/en/login`.
2. Enter valid credentials (e.g., Company Owner or Admin credentials).
3. Click on the **Login** button.
4. Upon successful authentication, the system redirects the user to the Dashboard URL: `https://dev.prowhats.com/en/dashboard`.
5. Navigate manually or via menu to the WhatsApp Chat URL: `https://dev.prowhats.com/en/contacts/whatsapp-chat`.

### 3.2 Default Page Loading Behavior
When the WhatsApp Chat page initializes, the system enforces the following default state:
- The **"All Messages"** main tab must be active by default.
- The **"All"** sub-tab must be active by default.

---

## 4. Conversation Tabs & Matrices

Users filter through conversations using a combination of main tabs and sub-tabs. Below is the behavioral matrix for these views.

### 4.1 Tab Mapping & Criteria
| Main Tab | Sub-Tab | Data Source / Filter Logic | Applicable Roles |
| :--- | :--- | :--- | :--- |
| **All Messages** | **All** | Displays all customer conversations where messages have been sent or received via the corporate WhatsApp number. | Owner, Admin, Agent |
| **Unattended** | **All** | Displays all customer conversations containing unread messages that have not been handled yet. | Owner, Admin, Agent |
| **Unattended** | **Mine** | Displays unread customer conversations that are strictly assigned to the currently authenticated user. | Owner, Admin, Agent |
| **Unattended** | **Unassigned** | Displays unread customer conversations that have not been assigned to any user. | Owner, Admin, Agent |
| **All** | **Mine** | Displays all conversations (read and unread) assigned to the logged-in user. | Owner, Admin, Agent |
| **All** | **Unassigned** | Displays all conversations that are not currently assigned to any Company Owner, Admin, or Agent. | Owner, Admin, Agent |

---

## 5. Feature Breakdown

### 5.1 Assign Conversation Flow
- **Preconditions:**
  1. User navigates to an **"Unassigned"** tab view.
  2. User selects an unassigned customer conversation from the list.
- **UI Elements:** The system displays an **"Assigned to me"** button.
- **Action Sequence:** 1. User clicks the **"Assigned to me"** button.
  2. The system binds the customer conversation to the logged-in user's account ID.
- **Post-Assignment Behavior:**
  - The system automatically triggers a redirection to the **"Mine"** tab view.
  - The newly assigned conversation must immediately appear inside the active user's assigned list.

### 5.2 See Contact Feature
- **Trigger:** User clicks the **"See contact"** button on an open conversation block.
- **Information Displayed:**
  - Customer phone number
  - Customer name
  - Customer country
  - Customer Gmail address
  - Assigned team
  - Assigned priority
  - Assigned conversation labels
- **Editable Parameters:** Company Owners, Admins, and Agents hold permissions to modify and save updates for:
  - Customer name
  - Customer country
  - Customer Gmail address
  - Assigned team
  - Assigned priority
  - Assigned conversation labels

### 5.3 Chat Filtering Features
Users can fine-tune their message lists dynamically via multi-parameter filters.
- **Filter by Status:** Limits views to selected conversation statuses:
  - `Open`
  - `Close`
  - `Pending`
  - `AI Agent`
- **Filter by Label:** Filters results to match the specified conversation label name.
- **Filter by Team:** Filters results to exclusively show conversations assigned to the designated team.

### 5.4 Manage Conversation Feature
- **Trigger:** User clicks the **"Manage"** button after choosing a customer conversation.
- **Modification Options:** The interface exposes fields allowing the user to update:
  - Assigned agent
  - Assigned team
  - Assigned label
  - Conversation status

---

## 6. Business Rules & Messaging Restrictions

### 6.1 Restriction: Unassigned Conversations
- **Rule:** Users are strictly blocked from broadcasting outbound text or media to unassigned customer channels.
- **Expected System Behavior:** - The message input viewport must be set to a disabled state, OR
  - Outbound transmission actions must be programmatically blocked.
  - Users must explicitly pull the chat into their **"Mine"** tab before interacting.

### 6.2 Restriction: 24-Hour WhatsApp Policy Window
- **Rule:** If the timestamp of the last message sent by the customer exceeds 24 hours relative to system time, standard outward communication is suspended.
- **Expected System Behavior:**
  - Outbound messaging forms must be disabled.
  - A descriptive validation warning must be displayed to inform the agent regarding the expiration of the 24-hour reply window.

---

## 7. Permissions Matrix

| Feature / Action | Company Owner | Admin | Agent |
| :--- | :---: | :---: | :---: |
| **View all conversations** | Yes | Yes | Yes |
| **View unattended conversations** | Yes | Yes | Yes |
| **Assign conversations** | Yes | Yes | Yes |
| **Assign conversation to self** | Yes | Yes | Yes |
| **View contact details** | Yes | Yes | Yes |
| **Update contact details** | Yes | Yes | Yes |
| **Filter conversations** | Yes | Yes | Yes |
| **Manage conversation** | Yes | Yes | Yes |
| **Send message from Mine tab** | Yes | Yes | Yes |
| **Send message to unassigned conversation** | **No** | **No** | **No** |
| **Send message after 24 hours** | **No** | **No** | **No** |

---

## 8. Data & Input Validations

- **Assignment Integrity:** Conversations must cleanly transition states from `Unassigned` to `Mine`. They must instantly disappear from unassigned filters and show up under the specific agent's bucket.
- **Messaging Barriers:** Outbound communication attempts must fail validation if the chat is unassigned or if the 24-hour WhatsApp session window has elapsed.
- **Filter Refreshing:** State mutations or adjustments to filters must immediately reload the active list view without displaying stale information or caching old results.
- **Contact Update Persistence:** Modifications executed via the "See Contact" interface must successfully write to the database and remain persistent across session refreshes.

---

## 9. Suggested Test Coverage

### 9.1 Functional Testing
- Verify system login with various role accounts.
- Validate tab and sub-tab selection permutations.
- Test the full conversation assignment pipeline and verify automatic view switching.
- Validate contact context modifications and data persistence checks.
- Test multi-tier filtering logic (Status, Label, Team combinations).
- Validate state transformations within the conversation manager dialogue.

### 9.2 UI Testing
- Ensure the active tab states match system conditions through visual styling highlights.
- Verify visibility and interaction constraints on contextual buttons.
- Confirm disabled UI states for text entries when interacting with unassigned chats or expired SLA blocks.
- Check view redirection animations and response behaviors following an assignment click.

### 9.3 Permission & Security Testing
- Execute role audits across Company Owner profiles, Admin panels, and Agent views to guarantee access alignments match the permissions matrix.

### 9.4 Negative Testing
- Attempt to inject out-of-bounds outbound messages into unassigned conversation items.
- Force-post messages to contacts beyond the 24-hour response window limit.
- Run edge-case or conflict-prone filtering parameters to ensure the listing defaults cleanly.
- Assess rendering configurations during empty states (e.g., when no chats match the filter criteria).