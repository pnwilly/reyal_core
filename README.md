# Reyal Core

Quality-of-life enhancements for Frappe / ERPNext. Provides shared utilities and settings used by other Reyal apps.

## Features

- **User display name formatting** — configure how user names appear across the system (Full Name, First + Last Initial, First Name Only)

## Installation

```bash
pip install -e apps/reyal_core
bench --site your.site install-app reyal_core
bench --site your.site migrate
```

## Settings

Go to **Reyal Settings** and configure:

| Setting | Description |
|---|---|
| User Display Name Format | How user names appear in notifications and references |
