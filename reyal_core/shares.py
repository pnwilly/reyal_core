import frappe

from reyal_core.naming import set_naming, set_naming_series

SHARE_TRANSFER_NAMING = "SHT-.DATEYY.DATEMM.#"
SHAREHOLDER_SERIES = "SH-.ABBR.-.#"


def set_share_naming():
	"""Name share transfers by their date and shareholders by their company, on sites with ERPNext."""
	if frappe.db.exists("DocType", "Share Transfer"):
		set_naming("Share Transfer", SHARE_TRANSFER_NAMING)
	if frappe.db.exists("DocType", "Shareholder"):
		set_naming_series("Shareholder", SHAREHOLDER_SERIES)
