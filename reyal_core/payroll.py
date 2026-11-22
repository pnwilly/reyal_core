import frappe

from reyal_core.naming import get_naming_date, set_naming, set_naming_series

PAYROLL_NAMING = {
	"Payroll Entry": "PROL-.ENDYY.ENDMM.#",
	"Salary Structure Assignment": "SSA-.FROMYY.FROMMM.#",
	"Salary Slip": "SS/.employee./.#",
}
PAYROLL_SERIES = {
	"Additional Salary": "ADS-.PAYYY.PAYMM.#",
	"Holiday List Assignment": "HLA-.FROMYY.FROMMM.#",
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


def payroll_year(doc, variable=None):
	"""Two-digit year of the Payroll Date, for the PAYYY naming variable."""
	return get_naming_date(doc, "payroll_date").strftime("%y")


def payroll_month(doc, variable=None):
	"""Two-digit month of the Payroll Date, for the PAYMM naming variable."""
	return get_naming_date(doc, "payroll_date").strftime("%m")


def set_payroll_naming():
	"""Name payroll documents by the period they cover, on sites that have HRMS."""
	for doctype, naming in PAYROLL_NAMING.items():
		if frappe.db.exists("DocType", doctype):
			set_naming(doctype, naming)
	for doctype, series in PAYROLL_SERIES.items():
		if frappe.db.exists("DocType", doctype):
			set_naming_series(doctype, series)
