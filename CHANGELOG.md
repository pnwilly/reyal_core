# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog.

## [Unreleased]


## [0.0.24] - 2026-11-24

### Fixed

- Keep the Series field hidden on new documents: ERPNext showed it on every new Stock Entry, Sales Invoice, Purchase Receipt, Journal Entry and other transactions, overriding the hidden setting

## [0.0.23] - 2026-11-24

### Changed

- Hide the Series field on every doctype whose series reyal_core sets, such as Stock Entry, Payment Entry and Sales Invoice; it was never the user's choice, and before saving it showed a default that reyal_core then replaced

## [0.0.22] - 2026-11-24

### Added

- Name Delivery Notes `DN-.POSTYY.POSTMM.#` and Stock Reconciliations `SRE-.POSTYY.POSTMM.##` by posting date, and Purchase Orders `PO-`, Material Requests `RQ-`, Quotations `QTN-` and Supplier Quotations `SQ-` by transaction date, on sites with ERPNext; these series were Kaida's and named by the day they were entered
- Offer Sales Invoices `INV-.YY.MM.#`, taken over from Kaida unchanged so invoices stay numbered in the order they are entered, and number returns `RINV-.YY.MM.#` in their own sequence; a return always takes `RINV-` and an invoice `INV-`, and a draft whose Is Return changes after saving cannot be saved
- Give returned Purchase Invoices, Purchase Receipts and Delivery Notes their `-RET-` series automatically from Is Return
- Name Stock Entries by purpose and posting date on sites with ERPNext, instead of `STX-` and the month they were created: `ST-` for Material Transfers, `MI-` for Material Issues, `MR-` for Material Receipts, `STM-` for Material Transfers for Manufacture and `SE-` for any other purpose, each followed by the posting year and month, so a March material issue entered in November is `MI-2503…`; a draft is renamed when its type or posting date changes

### Changed

- Report only whether the PR's checks passed in the comment posted once they finish, without mentioning the author; the assignment is the one notification

## [0.0.21] - 2026-11-23

### Added

- Name Assets `.ABBR.-.PURYY.PURMM.#` by company and purchase month, Asset Capitalizations `ASC-.POSTYY.POSTMM.#`, Asset Movements `ASM-.TRANSYY.TRANSMM.#`, Asset Repairs `ASR-.FAILYY.FAILMM.#` and Asset Value Adjustments `AVA-.DATEYY.DATEMM.#` on sites with ERPNext, with drafts renamed when their date or company moves them
- Add the `PURYY` and `PURMM` naming variables, read from Purchase Date, and `FAILYY` and `FAILMM`, read from Failure Date

### Changed

- Assign the PR author, then post the ready comment, once the PR's other checks have finished; the workflow used to comment without assigning

## [0.0.20] - 2026-11-23

### Added

- Name bills (Purchase Invoices) `Bill-.POSTYY.POSTMM.#`, or `Bill-RET-.POSTYY.POSTMM.#` for returns, on sites with ERPNext: the year and month come from the posting date, so a March invoice entered in November is named for March; a draft is renamed when its posting date moves it to another month
- Name Purchase Receipts `GR-.POSTYY.POSTMM.#` (returns `GR-RET-.POSTYY.POSTMM.#`) by posting date and Sales Orders `SO-.TRANSYY.TRANSMM.#` by transaction date, with drafts renamed when their date moves them to another month
- Add the `TRANSYY` and `TRANSMM` naming variables, read from Transaction Date

## [0.0.19] - 2026-11-23

### Added

- Name Salary Slips `SS/.employee./.#` on sites with HRMS, numbered per employee, instead of HRMS's `Sal Slip/<employee>/.#####`; submitted slips keep their names

## [0.0.18] - 2026-11-22

### Changed

- Mention the PR author only once the PR's other checks, CodeQL included, have finished, with their result, instead of as soon as the PR opens

## [0.0.17] - 2026-11-22

### Added

- Name Payroll Entries `PROL-.ENDYY.ENDMM.#` on sites with HRMS: the year and month come from the payroll period's end date, set on install and migrate; this moves the naming from Kaida so sites without Kaida get it
- Name Salary Structure Assignments `SSA-.FROMYY.FROMMM.#` on sites with HRMS: the year and month come from the From Date instead of the day the assignment is saved
- Name Share Transfers `SHT-.DATEYY.DATEMM.#` on sites with ERPNext: the year and month come from the transfer date
- Name Shareholders `SH-.ABBR.-.#` on sites with ERPNext: the Series field offers only this series, prefixed with the company abbreviation
- Number a new shareholder's folio `FN.##` instead of ERPNext's `FN.#####` when a Share Transfer leaves the folio blank
- Name Journal Entries `JE-.POSTYY.POSTMM.##` and Payment Entries `PMT-.POSTYY.POSTMM.#` (or `TRF-.POSTYY.POSTMM.#`) on sites with ERPNext: the year and month come from the posting date, so an entry posted to an earlier period is named for that period
- Name Additional Salaries `ADS-.PAYYY.PAYMM.#` and Holiday List Assignments `HLA-.FROMYY.FROMMM.#` on sites with HRMS
- Add the `DATEYY`, `DATEMM`, `POSTYY`, `POSTMM`, `PAYYY`, `PAYMM` and `ABBR` naming variables for any naming series
- Rename a saved draft named by a date when the date moves it to another period, moving its comments, attachments, to-dos and versions and giving back the old number when it was the last
- Give a Payment Entry the `TRF-` series when it is an Internal Transfer and `PMT-` otherwise; this moves the switch from Kaida so sites without Kaida get it

### Fixed

- Move a draft saved on a retired naming series, such as `JE-.YY.MM.##` or `ACC-JV-.YYYY.-`, to the current series when it is renamed for its period, instead of judging its name against the retired series and leaving it in place
- Keep a folio typed on a Share Transfer: the From and To Folio fields fill from the shareholder only when blank, instead of being cleared for a new shareholder and renumbered

## [0.0.16] - 2026-11-19

### Changed

- Show a saved email Communication as a message: a subject pinned under the top bar, a card with the sender, To, Cc and Bcc, failed-delivery and read-receipt chips, the whole message without an inner scroll box, and one collapsed Details section in place of the stock Status, More Information, Reference, Email Inbox and Timeline Links sections
- Show an email's direction and type in the title bar: a blue up-right arrow when sent, a green down-left arrow when received, and a list crumb named after the medium (Email, Phone, SMS…) that opens the list filtered by it; the sidebar shows the ID with the date to the minute and a short age (8 h ago)
- Show an address that belongs to a linked Contact by the Contact's saved name, with the address on hover
- List the reference and other linked documents on one Linked to line, one row per document type, using titles instead of IDs and Reyal short names for users; Contacts stay on the address lines, and Edit opens or closes the Timeline Links section

## [0.0.15] - 2026-11-11

### Changed

- Allow deleting a cancelled document that has been amended, behind the off-by-default Reyal Settings switch Allow Deleting Amended Originals; the amendment keeps its `amended_from` and `-1` name, a further amendment is still named `-2`, and the deleted document's series number is not reused
- Show View Amendment instead of the disabled Amend button on a cancelled document that has been amended
- Rename the Reyal Settings field User Short Display Name Format to Short Display Name Format; it already sits under Users

## [0.0.14] - 2026-11-11

### Fixed

- Opening a Desk notification marks it read and lowers the unread badge; Frappe V16 only cleared unread through "Mark all as read".

## [0.0.13] - 2026-10-28

### Changed

- Target Frappe V16 and attach notification actions to the sidebar notification view.

## [0.0.12] - 2026-09-03

### Changed

- Restore Frappe v15's native notification message rendering and vertical row spacing; retain Reyal's per-row controls and avatar grid

## [0.0.11] - 2026-08-29

### Changed

- Add automated Ruff linting, formatting, and pytest checks for pull requests
- Document local quality checks for contributors

## [0.0.10] - 2026-08-10

### Changed

- Restore the compact notifications dropdown layout: tighter row padding/margins, avatar|message grid, unread indicator under the avatar, and vertically centered delete/mark-as-read controls (kept the 0.0.9 HTML/media sanitizer so density does not reintroduce skew)
- Rename display title to **Reyal** (technical app name remains `reyal_core`)
- Clarify app description; add GitHub project URLs; declare bounded Frappe v15 dependency for Frappe Cloud; refresh license copyright years

## [0.0.9] - 2026-08-10

### Fixed

- Strip comment media (bare `<img>` and other rich HTML) from Notification Log descriptions in the Desk bell dropdown — prior sanitizers only matched email-style tags, so mention notifications with pasted photos still rendered full-size

## [0.0.8] - 2026-08-10

### Fixed

- Stop the notification MutationObserver from re-entering while decorating rows (was fragmenting one notification into avatar / text / mention slices each with a delete control)
- Only decorate real `a.notification-item[data-name]` rows
- Drop layout overrides that fought Frappe's notification row CSS; delete control stays top-right

## [0.0.7] - 2026-08-10

### Fixed

- Keep notification avatars at 36px (including `.standard-image` initials) so letters like "TO" no longer render as giant pink text in the dropdown

## [0.0.6] - 2026-08-10

### Fixed

- Collapse email-style HTML in the desk Notifications dropdown to a short plain-text line so Travel Request (and similar) bodies no longer skew into two columns
- Restore Frappe's flex notification row layout; keep the unread indicator beside the avatar and the mark-as-read control as a hover ring only

## [0.0.5] - 2026-08-09

### Fixed

- Keep rich HTML notification bodies stacked in a single column in the desk Notifications dropdown (avatar | message grid no longer lets email-style lists sit beside the greeting).

## [0.0.4] - 2026-05-03

### Fixed

- Build both the notification delete control and its dustbin icon with DOM APIs so CodeQL does not treat static icon markup as unsafe HTML.

## [0.0.3] - 2026-05-03

### Fixed

- Build the notification delete control structurally and set dynamic attributes via jQuery `.attr(...)` to avoid DOM HTML reinterpretation.

## [0.0.2] - 2026-05-03

### Added

- Desk Notifications row actions:
  - Per-notification delete icon in the toolbar Notifications dropdown.
  - Delete confirmation dialog before removing a notification.
  - Native Frappe `mark-as-read` behavior preserved while stacking controls vertically.
- Backend notification deletion endpoints for current-user scoped delete operations.

## [0.0.1] - 2026-04-18

### Added

- Initial `reyal_core` release with short user display name formatting support.
