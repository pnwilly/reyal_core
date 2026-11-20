import frappe
from frappe import _
from frappe.custom.doctype.property_setter.property_setter import make_property_setter
from frappe.utils import getdate

PAYROLL_NAMING = {
	"Payroll Entry": "PROL-.ENDYY.ENDMM.#",
	"Salary Structure Assignment": "SSA-.FROMYY.FROMMM.##",
}


def payroll_end_year(doc, variable=None):
	"""Two-digit year of the payroll period's end date, for the ENDYY naming variable."""
	return get_naming_date(doc, "end_date").strftime("%y")


def payroll_end_month(doc, variable=None):
	"""Two-digit month of the payroll period's end date, for the ENDMM naming variable."""
	return get_naming_date(doc, "end_date").strftime("%m")


def from_year(doc, variable=None):
	"""Two-digit year of the From Date, for the FROMYY naming variable."""
	return get_naming_date(doc, "from_date").strftime("%y")


def from_month(doc, variable=None):
	"""Two-digit month of the From Date, for the FROMMM naming variable."""
	return get_naming_date(doc, "from_date").strftime("%m")


def get_naming_date(doc, fieldname):
	value = doc.get(fieldname) if doc else None
	if not value:
		label = fieldname.replace("_", " ")
		frappe.throw(_("Set the {0} before naming this document.").format(label))
	return getdate(value)


def set_payroll_naming():
	"""Name payroll documents by the period they cover, on sites that have HRMS."""
	for doctype, naming in PAYROLL_NAMING.items():
		if frappe.db.exists("DocType", doctype):
			set_naming(doctype, naming)


def set_naming(doctype, naming):
	"""Set a doctype's naming through a Property Setter that Reyal owns."""
	setter = f"{doctype}-main-autoname"
	if not frappe.db.exists("Property Setter", setter):
		make_property_setter(
			doctype, None, "autoname", naming, "Data", for_doctype=True, is_system_generated=False
		)
	frappe.db.set_value("Property Setter", setter, {"value": naming, "module": "Reyal"})
	frappe.clear_cache(doctype=doctype)
