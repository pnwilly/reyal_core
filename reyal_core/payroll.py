import frappe
from frappe import _
from frappe.custom.doctype.property_setter.property_setter import make_property_setter
from frappe.utils import getdate

PAYROLL_ENTRY_NAMING = "PROL-.ENDYY.ENDMM.#"
PAYROLL_ENTRY_NAMING_SETTER = "Payroll Entry-main-autoname"


def payroll_end_year(doc, variable=None):
	"""Two-digit year of the payroll period's end date, for the ENDYY naming variable."""
	return get_payroll_end_date(doc).strftime("%y")


def payroll_end_month(doc, variable=None):
	"""Two-digit month of the payroll period's end date, for the ENDMM naming variable."""
	return get_payroll_end_date(doc).strftime("%m")


def get_payroll_end_date(doc):
	end_date = doc.get("end_date") if doc else None
	if not end_date:
		frappe.throw(_("Set the end date before naming the payroll entry."))
	return getdate(end_date)


def set_payroll_entry_naming():
	"""Name Payroll Entries by their period's end year and month, on sites that have HRMS."""
	if not frappe.db.exists("DocType", "Payroll Entry"):
		return
	if not frappe.db.exists("Property Setter", PAYROLL_ENTRY_NAMING_SETTER):
		make_property_setter(
			"Payroll Entry",
			None,
			"autoname",
			PAYROLL_ENTRY_NAMING,
			"Data",
			for_doctype=True,
			is_system_generated=False,
		)
	frappe.db.set_value(
		"Property Setter", PAYROLL_ENTRY_NAMING_SETTER, {"value": PAYROLL_ENTRY_NAMING, "module": "Reyal"}
	)
	frappe.clear_cache(doctype="Payroll Entry")
