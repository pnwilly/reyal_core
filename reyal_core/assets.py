import frappe

from reyal_core.naming import get_naming_date, set_naming, set_naming_series

ASSET_SERIES = {
	"Asset": ".ABBR.-.PURYY.PURMM.#",
	"Asset Capitalization": "ASC-.POSTYY.POSTMM.#",
	"Asset Repair": "ASR-.FAILYY.FAILMM.#",
}
ASSET_NAMING = {
	"Asset Movement": "ASM-.TRANSYY.TRANSMM.#",
	"Asset Value Adjustment": "AVA-.DATEYY.DATEMM.#",
}


def purchase_year(doc, variable=None):
	"""Two-digit year of the Purchase Date, for the PURYY naming variable."""
	return get_naming_date(doc, "purchase_date").strftime("%y")


def purchase_month(doc, variable=None):
	"""Two-digit month of the Purchase Date, for the PURMM naming variable."""
	return get_naming_date(doc, "purchase_date").strftime("%m")


def failure_year(doc, variable=None):
	"""Two-digit year of the Failure Date, for the FAILYY naming variable."""
	return get_naming_date(doc, "failure_date").strftime("%y")


def failure_month(doc, variable=None):
	"""Two-digit month of the Failure Date, for the FAILMM naming variable."""
	return get_naming_date(doc, "failure_date").strftime("%m")


def set_asset_naming():
	"""Name assets and their documents by the month they belong to, on sites with ERPNext."""
	for doctype, series in ASSET_SERIES.items():
		if frappe.db.exists("DocType", doctype):
			set_naming_series(doctype, series)
	for doctype, naming in ASSET_NAMING.items():
		if frappe.db.exists("DocType", doctype):
			set_naming(doctype, naming)
