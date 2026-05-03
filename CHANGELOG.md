# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog.

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
