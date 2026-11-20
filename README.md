# Reyal

Shared Reyal utilities for Frappe: short display names and Desk notification actions. Used by other Reyal apps.

## Features

- **User short display name formatting**: configure how user names appear across the system (First + Last Initial, or First + Middle Initial + Last Initial). Short names are applied in the desk UI, email headers, email Communication links, and @mention autocomplete.
- **Notification row actions in Desk**: adds a per-notification delete action in the toolbar Notifications dropdown.
- **Safe notification delete flow**: delete action requires explicit user confirmation before removing a notification.
- **Mark as read on open**: opening a notification marks just that notification read and lowers the unread badge. Frappe V16 otherwise only clears unread through "Mark all as read".
- **Email-style Communication form**: a saved email Communication reads like a message. The subject stays pinned under the top bar, an arrow in the title bar shows whether it was sent or received, and the card shows the sender, To/Cc/Bcc (linked Contacts by name), delivery and read chips, the whole message, and one Linked to line with a row per document type (users by their short display name). Technical fields collapse into Details, and Edit opens the stock Timeline Links section.
- **Deletable amended originals** (opt-in, Reyal Settings): Frappe's Amend works as usual, and a cancelled document that has been amended can still be deleted. The amendment keeps its `amended_from` and still saves, a further amendment is still named `-2`, and the deleted number is not reused. While both exist, the cancelled document shows View Amendment in place of the disabled Amend button.
- **Payroll Entry naming by period** (sites with HRMS): a Payroll Entry is named `PROL-` + the two-digit year and month of its end date + a running number, for example `PROL-26101` for the first October 2026 payroll. The `ENDYY` and `ENDMM` naming variables are available to other naming series too.

## Installation

```bash
bench get-app https://github.com/pnwilly/reyal_core --branch v16
bench --site your.site install-app reyal_core
bench --site your.site migrate
```

## Settings

Go to **Reyal Settings** and configure:

| Setting | Options |
|---|---|
| Users → Short Display Name Format | First + Last Initial, First + Middle Initial + Last Initial |
| Documents → Allow Deleting Amended Originals | Off (default), On |
