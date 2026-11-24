import frappe

from reyal_core.naming import set_naming_series

ACCOUNTING_SERIES = {
	"Journal Entry": ("JE-.POSTYY.POSTMM.##",),
	"Payment Entry": ("PMT-.POSTYY.POSTMM.#", "TRF-.POSTYY.POSTMM.#"),
	"Purchase Invoice": ("Bill-.POSTYY.POSTMM.#", "Bill-RET-.POSTYY.POSTMM.#"),
	"Purchase Receipt": ("GR-.POSTYY.POSTMM.#", "GR-RET-.POSTYY.POSTMM.#"),
	"Sales Order": ("SO-.TRANSYY.TRANSMM.#",),
	"Stock Entry": (
		"SE-.POSTYY.POSTMM.#",
		"ST-.POSTYY.POSTMM.#",
		"MI-.POSTYY.POSTMM.#",
		"MR-.POSTYY.POSTMM.#",
		"STM-.POSTYY.POSTMM.#",
	),
}

# Doctypes whose series follows a field: (field, {value: prefix}, prefix for any other value).
TYPED_SERIES = {
	"Payment Entry": ("payment_type", {"Internal Transfer": "TRF-"}, "PMT-"),
	"Stock Entry": (
		"purpose",
		{
			"Material Transfer": "ST-",
			"Material Transfer for Manufacture": "STM-",
			"Material Issue": "MI-",
			"Material Receipt": "MR-",
		},
		"SE-",
	),
}


def set_accounting_naming():
	"""Name journals, payments, bills, goods receipts, sales orders and stock entries by their month, on sites with ERPNext."""
	for doctype, series in ACCOUNTING_SERIES.items():
		if frappe.db.exists("DocType", doctype):
			set_naming_series(doctype, *series)
