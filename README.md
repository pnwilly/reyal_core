# Reyal

Shared Frappe utilities used by Reyal sites and apps.

## Requirements

| Branch | Frappe | Python |
|---|---|---|
| `v16` (default) | 16.x | 3.14+ |
| `v15` | 15.x | 3.10+ |

This README describes `v16`. Payroll naming needs HRMS and share naming needs ERPNext; everything else needs only Frappe.

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

## Document naming

Payroll and share documents are named after the period or company they belong to, not the day they are saved.

| Doctype | Naming | Example | Needs |
|---|---|---|---|
| Payroll Entry | `PROL-.ENDYY.ENDMM.#` | `PROL-26101`: first payroll ending October 2026 | HRMS |
| Salary Structure Assignment | `SSA-.FROMYY.FROMMM.#` | `SSA-26071`: first assignment from July 2026 | HRMS |
| Salary Slip | `SS/.employee./.#` | `SS/OCS_E01/1`: employee OCS_E01's first slip | HRMS |
| Share Transfer | `SHT-.DATEYY.DATEMM.#` | `SHT-24071`: first transfer dated July 2024 | ERPNext |
| Shareholder | `SH-.ABBR.-.#` (Series field) | `SH-OCS-1`: first shareholder of the company abbreviated OCS | ERPNext |
| Shareholder folio no. | `FN.##`, set by the first Share Transfer unless one is typed | `FN01`: the site's first folio | ERPNext |
| Journal Entry | `JE-.POSTYY.POSTMM.##` (Series field) | `JE-240701`: first journal posted in July 2024 | ERPNext |
| Payment Entry | `PMT-.POSTYY.POSTMM.#`, or `TRF-.POSTYY.POSTMM.#` for transfers (Series field) | `PMT-26101`: first payment posted in October 2026 | ERPNext |
| Purchase Invoice | `Bill-.POSTYY.POSTMM.#`, or `Bill-RET-.POSTYY.POSTMM.#` for returns (Series field) | `Bill-26031`: first bill posted in March 2026 | ERPNext |
| Purchase Receipt | `GR-.POSTYY.POSTMM.#`, or `GR-RET-.POSTYY.POSTMM.#` for returns (Series field) | `GR-26111`: first goods receipt posted in November 2026 | ERPNext |
| Sales Order | `SO-.TRANSYY.TRANSMM.#` (Series field) | `SO-26111`: first sales order dated November 2026 | ERPNext |
| Additional Salary | `ADS-.PAYYY.PAYMM.#` (Series field) | `ADS-26111`: first additional salary for November 2026 | HRMS |
| Holiday List Assignment | `HLA-.FROMYY.FROMMM.#` (Series field) | `HLA-26011`: first assignment from January 2026 | HRMS |

A saved draft is renamed when its dates move it to another period, for example a payment moved from 31 October to 2 November goes from `PMT-26101` to `PMT-26111`. Its comments, attachments, to-dos and version history move with it, and the old number is given back when it was the last one used. Submitted, cancelled and amended documents keep their names. A Payment Entry takes the `TRF-` series when it is an Internal Transfer and `PMT-` otherwise, on insert and when a draft's Payment Type changes.

Install and migrate set this naming. Other naming series can use the same variables: `ENDYY` and `ENDMM` read End Date, `FROMYY` and `FROMMM` read From Date, `DATEYY` and `DATEMM` read Date, `POSTYY` and `POSTMM` read Posting Date, `TRANSYY` and `TRANSMM` read Transaction Date, `PAYYY` and `PAYMM` read Payroll Date, and `ABBR` is the company's abbreviation.

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
