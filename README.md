# Reyal Core

Quality-of-life enhancements for Frappe. Provides shared utilities and settings used by other Reyal apps.

## Features

- **User short display name formatting**: configure how user names appear across the system (First + Last Initial, or First + Middle Initial + Last Initial). Short names are applied in the desk UI, email headers, and @mention autocomplete.
- **Notification row actions in Desk**: adds a per-notification delete action in the toolbar Notifications dropdown.
- **Safe notification delete flow**: delete action requires explicit user confirmation before removing a notification.
- **Native mark-as-read preserved**: keeps Frappe's native mark-as-read behavior and stacks it with delete in a compact vertical controls column.

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
| User Short Display Name Format | First + Last Initial, First + Middle Initial + Last Initial |
