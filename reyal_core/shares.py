import frappe
from frappe.model.naming import make_autoname

from reyal_core.naming import set_naming, set_naming_series, set_property

SHARE_TRANSFER_NAMING = "SHT-.DATEYY.DATEMM.#"
SHAREHOLDER_SERIES = "SH-.ABBR.-.#"
FOLIO_NAMING = "FN.##"
FOLIO_FIELDS = ("from_folio_no", "to_folio_no")


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
		keep_typed_folios()
	if frappe.db.exists("DocType", "Shareholder"):
		set_naming_series("Shareholder", SHAREHOLDER_SERIES)


def keep_typed_folios():
	"""Fill a Share Transfer folio from the shareholder only when it is blank, so a typed folio is kept."""
	for fieldname in FOLIO_FIELDS:
		setter = f"Share Transfer-{fieldname}-fetch_if_empty"
		set_property(setter, "Share Transfer", fieldname, "fetch_if_empty", "1", "Check")
	frappe.clear_cache(doctype="Share Transfer")
