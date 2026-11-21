import frappe
from frappe.model.naming import make_autoname

from reyal_core.naming import set_naming, set_naming_series

SHARE_TRANSFER_NAMING = "SHT-.DATEYY.DATEMM.#"
SHAREHOLDER_SERIES = "SH-.ABBR.-.#"
FOLIO_NAMING = "FN.##"


class ShareTransferFolio:
	"""Number a new shareholder's folio FN.## instead of ERPNext's FN.#####."""

	def autoname_folio(self, shareholder, is_company=False):
		doc = self.get_company_shareholder() if is_company else self.get_shareholder_doc(shareholder)
		doc.folio_no = make_autoname(FOLIO_NAMING)
		doc.save()
		return doc.folio_no


def set_share_naming():
	"""Name share transfers by their date and shareholders by their company, on sites with ERPNext."""
	if frappe.db.exists("DocType", "Share Transfer"):
		set_naming("Share Transfer", SHARE_TRANSFER_NAMING)
	if frappe.db.exists("DocType", "Shareholder"):
		set_naming_series("Shareholder", SHAREHOLDER_SERIES)
