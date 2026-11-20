import datetime
import importlib
import sys
from types import ModuleType, SimpleNamespace

import pytest


class ValidationError(Exception):
	pass


def load_payroll(monkeypatch, has_payroll_entry=True, has_setter=False):
	calls = []

	def throw(message):
		raise ValidationError(message)

	def exists(doctype, name):
		return has_payroll_entry if doctype == "DocType" else has_setter

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

	assert (payroll.payroll_end_year(october, "ENDYY"), payroll.payroll_end_month(october, "ENDMM")) == (
		"26",
		"10",
	)
	assert (payroll.payroll_end_year(june, "ENDYY"), payroll.payroll_end_month(june, "ENDMM")) == ("43", "06")


@pytest.mark.parametrize("doc", [None, {}, {"end_date": None}])
def test_end_date_is_required(monkeypatch, doc):
	payroll, _ = load_payroll(monkeypatch)

	with pytest.raises(ValidationError):
		payroll.payroll_end_year(doc, "ENDYY")


def test_naming_is_created_and_owned_by_reyal(monkeypatch):
	payroll, calls = load_payroll(monkeypatch)
	payroll.set_payroll_entry_naming()

	assert calls[0][0] == "make"
	assert calls[0][1] == ("Payroll Entry", None, "autoname", "PROL-.ENDYY.ENDMM.#", "Data")
	assert calls[1:] == [
		("set_value", "Payroll Entry-main-autoname", {"value": "PROL-.ENDYY.ENDMM.#", "module": "Reyal"}),
		("clear_cache", "Payroll Entry"),
	]


def test_existing_naming_is_updated_in_place(monkeypatch):
	payroll, calls = load_payroll(monkeypatch, has_setter=True)
	payroll.set_payroll_entry_naming()

	assert [call[0] for call in calls] == ["set_value", "clear_cache"]


def test_naming_is_skipped_without_hrms(monkeypatch):
	payroll, calls = load_payroll(monkeypatch, has_payroll_entry=False)
	payroll.set_payroll_entry_naming()

	assert calls == []
