import frappe

from reyal_core.naming import set_naming_series

ACCOUNTING_SERIES = {
	"Delivery Note": ("DN-.POSTYY.POSTMM.#", "DN-RET-.POSTYY.POSTMM.#"),
	"Journal Entry": ("JE-.POSTYY.POSTMM.##",),
	"Material Request": ("RQ-.TRANSYY.TRANSMM.#",),
	"Payment Entry": ("PMT-.POSTYY.POSTMM.#", "TRF-.POSTYY.POSTMM.#"),
	"Purchase Invoice": ("Bill-.POSTYY.POSTMM.#", "Bill-RET-.POSTYY.POSTMM.#"),
	"Purchase Order": ("PO-.TRANSYY.TRANSMM.#",),
	"Purchase Receipt": ("GR-.POSTYY.POSTMM.#", "GR-RET-.POSTYY.POSTMM.#"),
	"Quotation": ("QTN-.TRANSYY.TRANSMM.#",),
	# Sales Invoices stay numbered in the order they are entered, with returns in their own sequence.
	"Sales Invoice": ("INV-.YY.MM.#", "RINV-.YY.MM.#"),
	"Sales Order": ("SO-.TRANSYY.TRANSMM.#",),
	"Stock Entry": (
		"SE-.POSTYY.POSTMM.#",
		"ST-.POSTYY.POSTMM.#",
		"MI-.POSTYY.POSTMM.#",
		"MR-.POSTYY.POSTMM.#",
		"STM-.POSTYY.POSTMM.#",
	),
	"Stock Reconciliation": ("SRE-.POSTYY.POSTMM.##",),
	"Supplier Quotation": ("SQ-.TRANSYY.TRANSMM.#",),
}

# Doctypes whose series follows a field: (field, {value: prefix}, prefix for any other value).
TYPED_SERIES = {
	"Delivery Note": ("is_return", {1: "DN-RET-"}, "DN-"),
	"Payment Entry": ("payment_type", {"Internal Transfer": "TRF-"}, "PMT-"),
	"Purchase Invoice": ("is_return", {1: "Bill-RET-"}, "Bill-"),
	"Purchase Receipt": ("is_return", {1: "GR-RET-"}, "GR-"),
	"Sales Invoice": ("is_return", {1: "RINV-"}, "INV-"),
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
	"""Name sales, purchase, stock and accounting documents by their month, on sites with ERPNext."""
	for doctype, series in ACCOUNTING_SERIES.items():
		if frappe.db.exists("DocType", doctype):
			set_naming_series(doctype, *series)
