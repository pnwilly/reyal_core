import frappe
from frappe import _
from frappe.custom.doctype.property_setter.property_setter import make_property_setter
from frappe.utils import getdate


def date_year(doc, variable=None):
	"""Two-digit year of the Date field, for the DATEYY naming variable."""
	return get_naming_date(doc, "date").strftime("%y")


def date_month(doc, variable=None):
	"""Two-digit month of the Date field, for the DATEMM naming variable."""
	return get_naming_date(doc, "date").strftime("%m")


def posting_year(doc, variable=None):
	"""Two-digit year of the Posting Date, for the POSTYY naming variable."""
	return get_naming_date(doc, "posting_date").strftime("%y")


def posting_month(doc, variable=None):
	"""Two-digit month of the Posting Date, for the POSTMM naming variable."""
	return get_naming_date(doc, "posting_date").strftime("%m")


def transaction_year(doc, variable=None):
	"""Two-digit year of the Transaction Date, for the TRANSYY naming variable."""
	return get_naming_date(doc, "transaction_date").strftime("%y")


def transaction_month(doc, variable=None):
	"""Two-digit month of the Transaction Date, for the TRANSMM naming variable."""
	return get_naming_date(doc, "transaction_date").strftime("%m")


def company_abbr(doc, variable=None):
	"""The document's company abbreviation, for the ABBR naming variable."""
	company = doc.get("company") if doc else None
	if not company:
		frappe.throw(_("Set the company before naming this document."))
	return frappe.get_cached_value("Company", company, "abbr")


def get_naming_date(doc, fieldname):
	value = doc.get(fieldname) if doc else None
	if not value:
		label = fieldname.replace("_", " ")
		frappe.throw(_("Set the {0} before naming this document.").format(label))
	return getdate(value)


def set_naming(doctype, naming):
	"""Set a doctype's naming through a Property Setter that Reyal owns."""
	set_property(f"{doctype}-main-autoname", doctype, None, "autoname", naming, "Data")
	frappe.clear_cache(doctype=doctype)


def set_naming_series(doctype, *series):
	"""Offer these naming series on a doctype's Series field, the first as default, and hide the field.

	reyal_core picks the series itself, so the field is never the user's choice.
	"""
	values = {
		"options": ("\n".join(series), "Text"),
		"default": (series[0], "Text"),
		"hidden": ("1", "Check"),
	}
	for property_name, (value, property_type) in values.items():
		setter = f"{doctype}-naming_series-{property_name}"
		set_property(setter, doctype, "naming_series", property_name, value, property_type)
	frappe.clear_cache(doctype=doctype)


def set_property(setter, doctype, fieldname, property_name, value, property_type):
	if not frappe.db.exists("Property Setter", setter):
		make_property_setter(
			doctype,
			fieldname,
			property_name,
			value,
			property_type,
			for_doctype=not fieldname,
			is_system_generated=False,
		)
	frappe.db.set_value("Property Setter", setter, {"value": value, "module": "Reyal"})
