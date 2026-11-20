# Reyal

Shared Frappe utilities used by Reyal sites and apps.

## Requirements

| Branch | Frappe | Python |
|---|---|---|
| `v16` (default) | 16.x | 3.14+ |
| `v15` | 15.x | 3.10+ |

This README describes `v16`. Payroll naming needs HRMS; everything else needs only Frappe.

## Installation

```bash
bench get-app https://github.com/pnwilly/reyal_core --branch v16
bench --site your.site install-app reyal_core
bench --site your.site migrate
```

Use `--branch v15` on a Frappe v15 bench.

## Features

- **Short display names**: users appear as, for example, `Jane D.` in Desk, email sender names, @mentions and Communication links. Format set in Reyal Settings.
- **Notifications**: delete a row from the Notifications dropdown, after confirming. Opening a notification marks only that one as read.
- **Email Communication form**: a saved email reads like a message, with a pinned subject, a sent or received arrow, the sender and recipients (linked Contacts by name), delivery and read chips, and one Linked to line per document type.
- **Amended originals** (off by default): a cancelled document that has been amended can be deleted. The amendment keeps its name, and the deleted number is not reused.

## Payroll naming

On sites with HRMS, payroll documents are named after the period they cover, not the day they are saved.

| Doctype | Naming | Example |
|---|---|---|
| Payroll Entry | `PROL-.ENDYY.ENDMM.#` | `PROL-26101`: first payroll ending October 2026 |
| Salary Structure Assignment | `SSA-.FROMYY.FROMMM.##` | `SSA-260701`: first assignment from July 2026 |

Install and migrate set this naming. Other naming series can use the same variables: `ENDYY` and `ENDMM` read End Date, `FROMYY` and `FROMMM` read From Date.

## Settings

In **Reyal Settings**:

| Setting | Values | Default |
|---|---|---|
| Short Display Name Format | First + Last Initial, First + Middle Initial + Last Initial | First + Last Initial |
| Allow Deleting Amended Originals | Off, On | Off |

## Contributing

Branch workflow and local checks: [CONTRIBUTING.md](CONTRIBUTING.md). Changes: [CHANGELOG.md](CHANGELOG.md).

## License

MIT. See [license.txt](license.txt).
