import frappe
from frappe import _

from reyal_core.accounts import ACCOUNTING_SERIES

LINKED_ROWS = (
	("Comment", "reference_name", "reference_doctype"),
	("Communication", "reference_name", "reference_doctype"),
	("File", "attached_to_name", "attached_to_doctype"),
	("ToDo", "reference_name", "reference_type"),
	("Version", "docname", "ref_doctype"),
)


def set_draft_series(doc, method=None):
	"""Give a new Payment Entry the TRF series when it is an internal transfer, else PMT."""
	doc.naming_series = payment_series(doc)


def keep_draft_name_current(doc, method=None):
	"""Rename a saved draft whose name no longer matches its series and dates."""
	if doc.is_new() or doc.docstatus != 0 or doc.get("amended_from"):
		return
	series = series_for(doc)
	if not series:
		return
	previous = doc.get_doc_before_save()
	old_series = (previous.get("naming_series") or series_for(previous)) if previous else series
	if doc.meta.has_field("naming_series") and doc.naming_series != series:
		doc.naming_series = series
		if previous:
			previous.naming_series = series
	if not doc.name.startswith(get_prefix(series, doc)):
		rename_draft(doc, series, old_series, previous)


def series_for(doc):
	if doc.doctype == "Payment Entry":
		return payment_series(doc)
	if doc.meta.has_field("naming_series"):
		options = [option for option in (doc.meta.get_options("naming_series") or "").split("\n") if option]
		return doc.naming_series if doc.naming_series in options or not options else options[0]
	autoname = doc.meta.autoname or ""
	return autoname if "#" in autoname else None


def payment_series(doc):
	"""The PMT- or TRF- series for this payment, from the Series options reyal_core sets."""
	prefix = "TRF-" if doc.payment_type == "Internal Transfer" else "PMT-"
	options = (doc.meta.get_options("naming_series") or "").split("\n")
	series = next((option for option in options if option.startswith(prefix)), None)
	if not series:
		expected = next(s for s in ACCOUNTING_SERIES["Payment Entry"] if s.startswith(prefix))
		frappe.throw(_("Payment Entry has no {0} series. Migrate to set {1}.").format(prefix, expected))
	return series


def get_prefix(series, doc):
	from frappe.model.naming import NamingSeries

	return NamingSeries(series).get_prefix(doc)


def rename_draft(doc, series, old_series, previous=None):
	"""Rename a draft in place to the next name in series and give back its old number if it was the last.

	The open form follows the new name through localname. Only drafts of submittable doctypes are
	renamed, so no other document links to the old name.
	"""
	from frappe.model.naming import make_autoname, revert_series_if_last
	from frappe.model.rename_doc import rename_parent_and_child

	old_name = doc.name
	new_name = make_autoname(series, doc.doctype, doc)
	rename_parent_and_child(doc.doctype, old_name, new_name, doc.meta)
	rename_linked_rows(doc.doctype, old_name, new_name)
	revert_series_if_last(old_series, old_name, previous or doc)
	doc.name = new_name
	doc.localname = old_name
	for child in doc.get_all_children():
		child.parent = new_name


def rename_linked_rows(doctype, old_name, new_name):
	from frappe.query_builder import Field

	for table, name_field, type_field in LINKED_ROWS:
		frappe.qb.update(table).set(Field(name_field), new_name).where(
			(Field(type_field) == doctype) & (Field(name_field) == old_name)
		).run()
