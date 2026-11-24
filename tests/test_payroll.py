import pytest
from conftest import ValidationError

PAYROLL_DOCTYPES = ("Payroll Entry", "Salary Structure Assignment", "Salary Slip")


def test_end_date_sets_the_year_and_month(load_with_fake_frappe):
	payroll, _ = load_with_fake_frappe("reyal_core.payroll", PAYROLL_DOCTYPES)
	october = {"end_date": "2026-10-31"}
	june = {"end_date": "2043-06-30"}

	assert (payroll.payroll_end_year(october), payroll.payroll_end_month(october)) == ("26", "10")
	assert (payroll.payroll_end_year(june), payroll.payroll_end_month(june)) == ("43", "06")


def test_from_date_sets_the_year_and_month(load_with_fake_frappe):
	payroll, _ = load_with_fake_frappe("reyal_core.payroll", PAYROLL_DOCTYPES)
	assignment = {"from_date": "2026-07-01", "end_date": "2026-12-31"}

	assert (payroll.from_year(assignment, "FROMYY"), payroll.from_month(assignment, "FROMMM")) == ("26", "07")


def test_payroll_date_sets_the_year_and_month(load_with_fake_frappe):
	payroll, _ = load_with_fake_frappe("reyal_core.payroll", PAYROLL_DOCTYPES)
	additional_salary = {"payroll_date": "2026-11-30"}

	assert (payroll.payroll_year(additional_salary), payroll.payroll_month(additional_salary)) == ("26", "11")


@pytest.mark.parametrize(
	("variable", "doc"),
	[
		("payroll_end_year", None),
		("payroll_end_month", {}),
		("from_year", {"from_date": None}),
		("payroll_month", {}),
	],
)
def test_naming_date_is_required(load_with_fake_frappe, variable, doc):
	payroll, _ = load_with_fake_frappe("reyal_core.payroll", PAYROLL_DOCTYPES)

	with pytest.raises(ValidationError):
		getattr(payroll, variable)(doc)


def test_naming_is_created_and_owned_by_reyal(load_with_fake_frappe):
	payroll, calls = load_with_fake_frappe("reyal_core.payroll", PAYROLL_DOCTYPES)
	payroll.set_payroll_naming()

	assert [call[1][:4] for call in calls if call[0] == "make"] == [
		("Payroll Entry", None, "autoname", "PROL-.ENDYY.ENDMM.#"),
		("Salary Structure Assignment", None, "autoname", "SSA-.FROMYY.FROMMM.#"),
		("Salary Slip", None, "autoname", "SS/.employee./.#"),
	]
	assert [call for call in calls if call[0] == "set_value"] == [
		("set_value", "Payroll Entry-main-autoname", {"value": "PROL-.ENDYY.ENDMM.#", "module": "Reyal"}),
		(
			"set_value",
			"Salary Structure Assignment-main-autoname",
			{"value": "SSA-.FROMYY.FROMMM.#", "module": "Reyal"},
		),
		("set_value", "Salary Slip-main-autoname", {"value": "SS/.employee./.#", "module": "Reyal"}),
	]


def test_payroll_series_are_offered_on_the_series_field(load_with_fake_frappe):
	payroll, calls = load_with_fake_frappe(
		"reyal_core.payroll", ("Additional Salary", "Holiday List Assignment")
	)
	payroll.set_payroll_naming()

	assert [call[1][:4] for call in calls if call[0] == "make"] == [
		("Additional Salary", "naming_series", "options", "ADS-.PAYYY.PAYMM.#"),
		("Additional Salary", "naming_series", "default", "ADS-.PAYYY.PAYMM.#"),
		("Additional Salary", "naming_series", "hidden", "1"),
		("Holiday List Assignment", "naming_series", "options", "HLA-.FROMYY.FROMMM.#"),
		("Holiday List Assignment", "naming_series", "default", "HLA-.FROMYY.FROMMM.#"),
		("Holiday List Assignment", "naming_series", "hidden", "1"),
	]


def test_existing_naming_is_updated_in_place(load_with_fake_frappe):
	payroll, calls = load_with_fake_frappe(
		"reyal_core.payroll", ("Payroll Entry",), setters=("Payroll Entry-main-autoname",)
	)
	payroll.set_payroll_naming()

	assert [call[0] for call in calls] == ["set_value", "clear_cache"]


def test_naming_is_skipped_without_hrms(load_with_fake_frappe):
	payroll, calls = load_with_fake_frappe("reyal_core.payroll")
	payroll.set_payroll_naming()

	assert calls == []
