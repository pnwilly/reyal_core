# Reyal

Shared Reyal utilities for Frappe: short display names and Desk notification actions. Used by other Reyal apps.

## Features

- **User short display name formatting**: configure how user names appear across the system (First + Last Initial, or First + Middle Initial + Last Initial). Short names are applied in the desk UI, email headers, and @mention autocomplete.
- **Notification row actions in Desk**: adds a per-notification delete action in the toolbar Notifications dropdown.
- **Safe notification delete flow**: delete action requires explicit user confirmation before removing a notification.
- **Mark as read on open**: opening a notification marks just that notification read and lowers the unread badge. Frappe V16 otherwise only clears unread through "Mark all as read".
- **Deletable amended originals**: Frappe's Amend works as usual, and a cancelled document that has been amended can still be deleted. The amendment keeps its `amended_from` and still saves, a further amendment is still named `-2`, and the deleted number is not reused. While both exist, the cancelled document shows View Amendment in place of the disabled Amend button.

## Installation

```bash
bench get-app https://github.com/pnwilly/reyal_core
bench --site your.site install-app reyal_core
bench --site your.site migrate
```

## Settings

Go to **Reyal Settings** and configure:

| Setting | Options |
|---|---|
| Users → Short Display Name Format | First + Last Initial, First + Middle Initial + Last Initial |
