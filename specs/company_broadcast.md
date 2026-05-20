# ProWhats Broadcast Page Specification

## Module
Broadcast / Campaign Management

---

# 1. Functional Requirements

## Broadcasts Listing Dashboard

### Listing Visibility
- Displays all broadcasts (sent or scheduled) for the specific company
- Accessible only to authenticated users

---

### Dashboard Columns
- **Name:** The campaign name
- **Template:** WhatsApp message template utilized
- **Created on Date:** Timestamp of creation
- **Schedule:** Scheduled time (or `--` if instant)
- **Contacts:** Count of target contacts
- **Status:** Completed, Running, Scheduled, Pending, or Cancelled

---

### Actions Menu
- **View Details:** Clickable option from the table to view detailed metrics of the broadcast

---

## Broadcast Details Page

### Details View Metrics
Displays specific metrics for the selected broadcast:
- **Run Percentage:** Percentage of the broadcast completed
- **Total Messages:** Total count of messages in the campaign
- **WhatsApp Sent:** Messages successfully sent through the network
- **Errors:** Messages that failed or were not sent
- **In Progress:** Messages currently sending
- **Delivered:** Messages successfully delivered to recipients
- **Read:** Messages read by recipients

---

## Create a New Broadcast Flow

### Navigation
Redirects to:
`https://dev.prowhats.com/en/broadcast/create`

---

### Create Broadcast Fields

#### Name Field
- Required
- Text input for broadcast name
- Max length: 255 characters

#### Template Selection
- Required
- Dropdown to select approved message template

#### Target Audience Selection
- Required
- Select from Contact Group or Labels

#### Schedule Options
- Required
- Select specific Date/Time OR
- Check "Ignore scheduled time and send now" for immediate send

#### Submission Buttons
- **Apply:** Validates configurations (remains disabled if fields missing)
- **Send Campaign:** Final action to dispatch the broadcast

---

# 2. Role-Based Access

## Company Owner
Can view and access:
**Yes**

---

## Admin
Can view and access:
**Yes**

---

## Agent
Can view and access:
**No**
Redirect:
**Dashboard / Access Denied**

---

# 3. Validation Rules

## Broadcast Name
Reject:
- Empty field
- Only spaces
- Exceeds maximum length

Error:
`Campaign name is required` or `Maximum length exceeded`

---

## Schedule Date
Reject:
- Dates in the past

Error:
`Invalid schedule time`

---

# 4. Security Requirements

## Unauthorized Access
Direct URL access blocked without login

Example:
Attempt:
`/en/broadcast`

Expected:
Redirect to Login page

---

## Unauthorized Role Access
Example:
Attempt: Agent visits `/en/broadcast`

Expected:
Blocked (403 Forbidden) or Redirect to safe page

---

# 5. Responsive Requirements

## Large Desktop
Resolution:
2560x1440

Expected:
- Table columns fully visible
- Proper whitespace usage
- Forms properly aligned

---

## Standard Desktop
Resolution:
1920x1080

Expected:
- Proper alignment and spacing
- Full visibility of metrics charts

---

## Laptop
Resolution:
1366x768

Expected:
- Fully visible without overflow
- Broadcast table clear and readable

---

## Tablet Landscape
Resolution:
1024x768

Expected:
- Responsive horizontal layout
- Table may become horizontally scrollable

---

## Tablet Portrait
Resolution:
768x1024

Expected:
- Responsive stacked layout
- Create broadcast forms collapse to single column

---

## Large Mobile
Device:
iPhone 14 Pro Max

Resolution:
430x932

Expected:
- Sidebar menu becomes a hamburger menu
- Details page metrics stack vertically
- Touch-friendly controls

---

## Standard Mobile
Device:
iPhone 12 / 13

Resolution:
390x844

Expected:
- Broadcast table converts to card-views or horizontal scroll
- Buttons clickable
- No horizontal layout breaking

---

# 6. Test Scenarios

## Positive Tests
- Successful Scheduled Broadcast
- Successful Instant Broadcast
- Admin Login & Access
- Owner Login & Access
- View Broadcast Details Page Data

---

## Negative Tests
- Unauthenticated Access
- Agent Access Attempt
- Missing Required Fields on Create
- Past Date Scheduling
- Double Submission on Send Campaign

---

## Validation Edge Cases
- Zero Contacts in Group
- Template Variable Mismatch
- Massive Broadcast Data Load (Performance)
- Network Disconnection During Send

---

## Responsive Tests
- Mobile
- Tablet
- Desktop

---

## Cross Browser Tests
All supported browsers
