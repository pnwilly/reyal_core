import frappe

from reyal_core.naming import set_naming_series

ACCOUNTING_SERIES = {
	"Journal Entry": ("JE-.POSTYY.POSTMM.##",),
	"Payment Entry": ("PMT-.POSTYY.POSTMM.#", "TRF-.POSTYY.POSTMM.#"),
}


def set_accounting_naming():
	"""Name journal and payment entries by their posting month, on sites with ERPNext."""
	for doctype, series in ACCOUNTING_SERIES.items():
		if frappe.db.exists("DocType", doctype):
			set_naming_series(doctype, *series)
