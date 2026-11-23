import frappe

from reyal_core.naming import set_naming_series

ACCOUNTING_SERIES = {
	"Journal Entry": ("JE-.POSTYY.POSTMM.##",),
	"Payment Entry": ("PMT-.POSTYY.POSTMM.#", "TRF-.POSTYY.POSTMM.#"),
	"Purchase Invoice": ("Bill-.POSTYY.POSTMM.#", "Bill-RET-.POSTYY.POSTMM.#"),
	"Purchase Receipt": ("GR-.POSTYY.POSTMM.#", "GR-RET-.POSTYY.POSTMM.#"),
	"Sales Order": ("SO-.TRANSYY.TRANSMM.#",),
}


def set_accounting_naming():
	"""Name journals, payments, bills, goods receipts and sales orders by their month, on sites with ERPNext."""
	for doctype, series in ACCOUNTING_SERIES.items():
		if frappe.db.exists("DocType", doctype):
			set_naming_series(doctype, *series)
