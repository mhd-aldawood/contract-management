# Contract Management UI Design System

The frontend is designed as an Arabic-first, right-to-left administrative application for Syrian users.

## Global theme

All global colors, typography, spacing, radii, shadows, and content width are CSS variables at the top of:

`src/assets/styles/theme.css`

Change variables such as `--color-primary-700`, `--color-canvas`, `--radius-lg`, or `--content-width` once to update the complete application.

## Shared components

- `AppToolbar.vue`: persistent CRM-style RTL sidebar, grouped navigation, account display, logout, and responsive mobile drawer.
- `PageHeader.vue`: page title, description, section label, icon, and primary actions.
- `BaseModal.vue`: shared dialog with generous desktop widths, a full-screen phone layout, one scrolling body, and persistent header/footer actions.
- `ModalFormActions.vue`: places agreement Save and visibility controls in the enclosing dialog footer; standalone forms keep them inline.
- `StatusBadge.vue`: consistent active, inactive, warning, and informational states.
- `FormRow.vue`: shared contract form row, labels, validation, and responsive layout.
- `NotificationHost.vue`: global success and error feedback.
- `PasswordField.vue`: the only password-input pattern; includes a visible, accessible show/hide control that cannot inherit primary-button sizing.

## Page patterns

### Dashboard

Keep the page and sidebar title **لوحة التحكم**. `GET /api/dashboard/` supplies live counters, agreement types, date-based phases, six months of creation activity and the five most recently updated agreements. Admin sees user/role and Finance summaries; Dean sees aggregate user counts, all agreements and Finance coverage; Finance focuses on orders, documents without orders and recent uploads; Contracts focuses on creation, reminders and expiration; Planning includes only visible agreements. The API applies feature permissions before aggregation; Home access alone does not expose agreement, user or Finance data. Dean user counts do not grant access to user records.

Use `DashboardDonut` with visible numeric legends and theme colors. Avoid hard-coded sample numbers. Show zero counts and informative empty states when no data exists. New means created this calendar month; current/future/finished use agreement dates in Damascus time. Order coverage counts active files, not paid amounts. Quick links use current feature permissions and chart type links open filtered lists; recent agreement links select the document in Dean/Finance or filter its list.

### List and management pages

1. Use `PageHeader` with the main add action.
2. Place filters inside the shared `.filters` surface.
3. Place results in `.table-scroll` or `.table-container`.
4. Use `StatusBadge` for state instead of color-only text.
5. Keep edit, activate, and deactivate actions in the row.
6. Open add and update forms in `BaseModal`.
7. Use danger styling only for destructive or deactivation actions.
8. Contract routes use `ContractListView.vue`: load saved records for the route's feature, filter and paginate the list, and open creation inside `BaseModal`. A successful save closes the modal and reloads the same list.
9. Calendar inputs use left-to-right date segments inside the Arabic layout. Display calendar dates with `formatContractDate` to avoid time-zone shifts.

### Modal and form layout

Use the shared modal width tokens in `theme.css`: `sm` 36rem, `md` 52rem, `lg` 76rem, and `xl` 88rem. Agreement forms and details use `lg`; user and role forms use `md`. Widths are limited by the available viewport with comfortable outer margins. Short dialogs keep their natural height; long dialogs use the available viewport height. Below 640px, dialogs fill the screen and account for safe-area insets.

Only `.base-modal__body` scrolls vertically. Header, close, Save and Cancel remain visible. Do not give nested permission lists or form sections their own height limit or vertical scrollbar. User role permissions are an expandable preview. Form grids switch based on the dialog's content width, including tablets; use two columns for ordinary fields and three for dates on wide agreement dialogs, then one column on smaller screens. Place labels above controls, keep errors beside the affected field, and group agreement data, dates, payments, status and attachments in named sections. Payment rows become labeled cards instead of squeezed tables. Use `ModalFormActions` for long agreement forms so Save remains reachable without scrolling to the bottom.

### Navigation organization

The sidebar groups every feature as an independent destination:

1. Main: dashboard, planning, finance, and Dean agreement review.
2. Contracts: each agreement type has its own item.
3. System administration: Settings, Users, and Roles are separate destinations, visible to Admin.
4. Account: profile and system information. Other authorized roles retain their personal Settings link here.

Role management selects one role from a dropdown and displays its features vertically. User-role assignment belongs only to User Management.

### Contract form pages

Planning loads `GET /api/planning/agreements/`, which requires Planning read permission and returns all agreement types with `isHidden=false`. The same rule applies when an administrator opens Planning. Hidden records remain on their authorized contract management pages.

The API returns `planningPhase` independently of the manually entered `status`: both dates before today means `finish`, both after today means `future`, and a range including today means `current`. Today is the calendar day in `Asia/Damascus`. Missing or reversed dates are `unknown`. The optional API filter is `?phase=finish|current|future|unknown`. Clearing Hide makes a saved agreement available on the next Planning refresh.

1. Use `.agreement-section` and `.pdf-content`.
2. Use `FormRow` for fields and validation feedback.
3. Keep the main save action at the bottom-right in RTL layout.
4. Display read-only access with `.read-only-notice`.
5. Use Arabic labels and `ar-SY` formatting for user-facing dates and numbers.

### Authentication pages

1. Use `.auth-page` or `.auth-wrapper` with `.auth-card`.
2. Keep labels visible; placeholders never replace labels.
3. Preserve password visibility controls and browser autocomplete attributes.
4. Always use `PasswordField.vue` for password inputs. Do not create raw `type="password"` fields or page-specific eye buttons.

## Language and accessibility

Finance (`/finance`) has three agreement columns: name, number, and details. Following the School Management payment workspace pattern, selecting an agreement highlights its row and loads its disbursement orders in the section below the agreement list. The section shows the selected agreement, count, download, multi-file upload, editable order name/notes, single-file replacement, and inline removal confirmation. Switching documents clears the previous results and ignores stale responses; successful changes reload only the selected agreement's orders and update its count. File replacement keeps the same order ID. Removal excludes only that order from active lists. Finance read/write permissions are independent of agreement editing; Finance and Admin manage orders by default, Dean can read them. Admin can configure this feature in the role matrix. Hidden agreements are included in Finance because hiding applies to Planning.

Order files are stored below `media/private/disbursement-orders/`; Nginx blocks direct `/media/private/` access. Files must be downloaded through the authenticated Finance or Dean API. Uploads support up to 20 files and 19 MiB total per request.

Dean review (`/dean`) follows the selectable agreement table and lower detail workspace in `t.html`. It includes all agreement types and hidden records, with search, type and Planning visibility filters. Selecting a document shows its fields, clauses, payment schedule, attachment, and active Finance orders. Order downloads require Dean read permission. The persisted Planning visibility switch requires Dean write permission and changes only `isHidden`; hiding removes the agreement from the next Planning refresh, and showing restores it. Admin and Dean receive this feature by default; Admin can configure read/write permissions in Roles. Switching documents discards stale detail responses.

- The document declares `lang="ar"` and `dir="rtl"`.
- Primary interface text is Arabic.
- Interactive icons include Arabic accessible labels.
- Keyboard focus uses the global focus ring.
- Status is communicated with text and color.
- Tables remain horizontally scrollable on narrow screens.
- Modals prevent background scrolling and fill the viewport on phones.
