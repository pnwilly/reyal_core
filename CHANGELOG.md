# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog.

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
