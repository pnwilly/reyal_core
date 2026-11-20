import datetime
import importlib
import sys
from types import ModuleType, SimpleNamespace

import pytest


class ValidationError(Exception):
	pass


def load_payroll(monkeypatch, doctypes=("Payroll Entry", "Salary Structure Assignment"), setters=()):
	calls = []

	def throw(message):
		raise ValidationError(message)

	def exists(doctype, name):
		return name in (doctypes if doctype == "DocType" else setters)

	fake_frappe = ModuleType("frappe")
	fake_frappe._ = lambda text: text
	fake_frappe.throw = throw
	fake_frappe.clear_cache = lambda doctype: calls.append(("clear_cache", doctype))
	fake_frappe.db = SimpleNamespace(
		exists=exists,
		set_value=lambda doctype, name, values: calls.append(("set_value", name, values)),
	)
	fake_utils = ModuleType("frappe.utils")
	fake_utils.getdate = lambda value: datetime.date.fromisoformat(value)
	fake_property_setter = ModuleType("frappe.custom.doctype.property_setter.property_setter")
	fake_property_setter.make_property_setter = lambda *args, **kwargs: calls.append(("make", args, kwargs))
	modules = {
		"frappe": fake_frappe,
		"frappe.utils": fake_utils,
		"frappe.custom": ModuleType("frappe.custom"),
		"frappe.custom.doctype": ModuleType("frappe.custom.doctype"),
		"frappe.custom.doctype.property_setter": ModuleType("frappe.custom.doctype.property_setter"),
		"frappe.custom.doctype.property_setter.property_setter": fake_property_setter,
	}
	for name, module in modules.items():
		monkeypatch.setitem(sys.modules, name, module)

	import reyal_core.payroll as payroll

	return importlib.reload(payroll), calls


def test_end_date_sets_the_year_and_month(monkeypatch):
	payroll, _ = load_payroll(monkeypatch)
	october = {"end_date": "2026-10-31"}
	june = {"end_date": "2043-06-30"}

	assert (payroll.payroll_end_year(october), payroll.payroll_end_month(october)) == ("26", "10")
	assert (payroll.payroll_end_year(june), payroll.payroll_end_month(june)) == ("43", "06")


def test_from_date_sets_the_year_and_month(monkeypatch):
	payroll, _ = load_payroll(monkeypatch)
	assignment = {"from_date": "2026-07-01", "end_date": "2026-12-31"}

	assert (payroll.from_year(assignment, "FROMYY"), payroll.from_month(assignment, "FROMMM")) == ("26", "07")


@pytest.mark.parametrize(
	("variable", "doc"),
	[("payroll_end_year", None), ("payroll_end_month", {}), ("from_year", {"from_date": None})],
)
def test_naming_date_is_required(monkeypatch, variable, doc):
	payroll, _ = load_payroll(monkeypatch)

	with pytest.raises(ValidationError):
		getattr(payroll, variable)(doc)


def test_naming_is_created_and_owned_by_reyal(monkeypatch):
	payroll, calls = load_payroll(monkeypatch)
	payroll.set_payroll_naming()

	assert [call[1][:4] for call in calls if call[0] == "make"] == [
		("Payroll Entry", None, "autoname", "PROL-.ENDYY.ENDMM.#"),
		("Salary Structure Assignment", None, "autoname", "SSA-.FROMYY.FROMMM.##"),
	]
	assert [call for call in calls if call[0] == "set_value"] == [
		("set_value", "Payroll Entry-main-autoname", {"value": "PROL-.ENDYY.ENDMM.#", "module": "Reyal"}),
		(
			"set_value",
			"Salary Structure Assignment-main-autoname",
			{"value": "SSA-.FROMYY.FROMMM.##", "module": "Reyal"},
		),
	]


def test_existing_naming_is_updated_in_place(monkeypatch):
	payroll, calls = load_payroll(
		monkeypatch, doctypes=("Payroll Entry",), setters=("Payroll Entry-main-autoname",)
	)
	payroll.set_payroll_naming()

	assert [call[0] for call in calls] == ["set_value", "clear_cache"]


def test_naming_is_skipped_without_hrms(monkeypatch):
	payroll, calls = load_payroll(monkeypatch, doctypes=())
	payroll.set_payroll_naming()

	assert calls == []
