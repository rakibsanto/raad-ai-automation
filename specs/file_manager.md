## 1. Module Overview
- **Module Name:** File Manager
- **Description:** The File Manager page allows Company Owner, Admin, and Agent users to upload, store, categorize, and manage various media and document files. Users can retrieve persistent URLs for uploaded assets to share with customers, track storage usage via a progress bar, and switch between list and grid views.

---

## 2. System URLs & Access

### 2.1 Web Endpoints
| Page / Action | URL |
| :--- | :--- |
| **Base URL** | `https://dev.prowhats.com/en` |
| **Login URL** | `https://dev.prowhats.com/en/login` |
| **Dashboard URL** | `https://dev.prowhats.com/en/dashboard` |
| **File Manager URL** | `https://dev.prowhats.com/en/files` |

### 2.2 System Roles
- **Company Owner**
- **Admin**
- **Agent**

## 3. Core Workflows

### 3.1 Login & Navigation Flow
1. Open the Base/Login URL: `https://dev.prowhats.com/en/login`.
2. Enter valid credentials (e.g., Company Owner or Admin credentials).
3. Click on the **Login** button.
4. Upon successful authentication, the system redirects the user to the Dashboard URL: `https://dev.prowhats.com/en/dashboard`.
5. Navigate manually or via menu to the File Manager URL: `https://dev.prowhats.com/en/files`.

### 3.2 Default Page Loading Behavior
When the File Manager page initializes, the system enforces the following default state:
- The **"All"** files tab must be active by default.
- The default data display layout must be set to **List View** (or the system-specified default).
- The storage usage progress bar must dynamically calculate and display current storage metrics.

---

## 4. File Categorization Tabs & Layout Matrices

Users filter through their uploaded assets using a combination of categorization tabs and view layout modifiers.

### 4.1 Tab Mapping & Filter Criteria
| Active Tab | Allowed File Types / Extension Matching | Applicable Roles |
| :--- | :--- | :--- |
| **All** | Displays every uploaded file regardless of format (Images, Videos, Audios, Docs). | Owner, Admin, Agent |
| **Image** | Filters and displays only image files (e.g., `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`). | Owner, Admin, Agent |
| **Video** | Filters and displays only video files (e.g., `.mp4`, `.mkv`, `.avi`, `.mov`). | Owner, Admin, Agent |
| **Audio** | Filters and displays only audio files (e.g., `.mp3`, `.wav`, `.ogg`, `.aac`). | Owner, Admin, Agent |
| **Docs** | Filters and displays document formats (e.g., `.pdf`, `.docx`, `.xlsx`, `.txt`, `.csv`). | Owner, Admin, Agent |

### 4.2 Layout View States
- **List View:** Displays file rows with columns for file name, type/extension, actions (Copy, Download, Delete), and timestamp details.
- **Grid View:** Displays files as visual thumbnails or icon cards, optimized for quick media preview and quick actions.

---

## 5. Feature Breakdown

### 5.1 File Upload Pipeline
- **Supported Formats:** Audio, Video, Image, and Document files.
- **Action Sequence:** 1. User clicks the upload target area or drags a file into the upload zone.
  2. The system processes the file, saves it to storage, and generates a permanent web URL.
- **Post-Upload Behavior:** - The storage progress bar metrics update immediately.
  - The newly uploaded file automatically populates at the top of the active file table/grid.

### 5.2 Copy URL & Share Feature
- **Trigger:** User clicks the **"Copy Link/URL"** action button associated with a specific file row or card.
- **Expected System Behavior:** The full persistent URL of the file is saved to the user's system clipboard.
- **Business Purpose:** Allows users to easily paste and share direct media links with customers across communication streams.

### 5.3 Download Asset Feature
- **Trigger:** User clicks the **"Download"** button on an asset.
- **Expected System Behavior:** Triggers a native browser file download prompt to fetch the raw file directly onto local system storage.

### 5.4 Delete Asset Feature
- **Trigger:** User clicks the **"Delete"** button on an asset.
- **Expected System Behavior:** Triggers a confirmation dialogue. Upon confirmation, the asset is removed from the database, the URL is invalidated, the file list refreshes, and space is freed on the storage progress bar.

### 5.5 Storage Progress Bar Tracking
- **UI Elements:** A persistent visual progress bar displaying used storage versus allocated limits.
- **Information Displayed:** Displays total uploaded file size metrics formatted dynamically in Megabytes (MB) or Gigabytes (GB).

---

## 6. Business Rules & Layout Constraints

### 6.1 Constraint: Layout State Continuity
- Changing between **List View** and **Grid View** layout states must not alter or reset the currently selected categorization tab (e.g., if on the "Video" tab, toggling grid view must still filter exclusively for videos).

### 6.2 Search Interactivity
- Typing in the search bar must dynamically filter files **by name** in real-time or upon pressing Enter. Search constraints must apply within the scope of the currently active categorization tab.

### 6.3 Pagination Controls
- The file data presentation elements must enforce strict pagination limits per page. Changing pages must cleanly load the next block of data without caching old assets or displaying stale rows.

---

## 7. Permissions Matrix

| Feature / Action | Company Owner | Admin | Agent |
| :--- | :---: | :---: | :---: |
| **Access / View File Manager page** | Yes | Yes | Yes |
| **Upload Audio, Video, Image, Docs** | Yes | Yes | Yes |
| **Switch Categories (All/Image/Video/Audio/Docs)**| Yes | Yes | Yes |
| **Toggle Grid View / List View** | Yes | Yes | Yes |
| **Search by File Name** | Yes | Yes | Yes |
| **Copy File URL to Clipboard** | Yes | Yes | Yes |
| **Download Files** | Yes | Yes | Yes |
| **Delete Files** | Yes | Yes | Yes |
| **View Storage Metrics / Progress Bar** | Yes | Yes | Yes |

---

## 8. Data & Input Validations

- **Tab Isolation Integrity:** When a specific category tab is chosen, files belonging to other categories must be completely hidden.
- **Storage Calculation Precision:** Uploading or deleting a file must instantaneously update the progress bar calculations accurately down to the correct MB/GB value.
- **Search Scope Resolution:** Clearing a search keyword must instantly return the file view back to the full uncensored listing matching the active tab criteria.

---

## 9. Suggested Test Coverage

### 9.1 Functional Testing
- Verify successful authentication and direct route navigation targeting the `/files` endpoint.
- Validate the file upload pipeline across multiple formats (`.mp4`, `.png`, `.mp3`, `.pdf`).
- Test "Copy URL" functionality to ensure a valid clipboard payload is created.
- Validate Search bar accuracy when filtering for partial and exact match file names.
- Verify file deletion and confirm that the item is completely removed from the listing.

### 9.2 UI Testing
- Verify the active styling highlights properly identify the selected category tab.
- Test responsive rendering constraints when toggling between Grid View and List View.
- Check the visual completeness and text formatting accuracy (MB/GB) on the storage progress bar.
- Ensure pagination page numbers and previous/next arrows behave correctly.

### 9.3 Security Testing
- Verify route protection models to ensure unauthenticated guest users are strictly blocked from accessing `/files` directly and are kicked back to the login page.
- Run audits across Owner, Admin, and Agent accounts to confirm feature consistency across all profiles.

### 9.4 Negative Testing
- Attempt to execute searches with specialized regex characters to ensure search fields handle text sanitization cleanly without throwing system errors.
- Confirm that file queries matching zero results render a clean, user-friendly empty state screen.