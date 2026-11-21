import datetime
import importlib
import sys
from types import ModuleType, SimpleNamespace

import pytest


class ValidationError(Exception):
	pass


@pytest.fixture
def load_with_fake_frappe(monkeypatch):
	"""Import a reyal_core module against a fake frappe; return the module and the recorded calls."""

	def load(module_name, doctypes=(), setters=(), abbrs=None):
		calls = []

		def throw(message):
			raise ValidationError(message)

		def exists(doctype, name):
			return name in (doctypes if doctype == "DocType" else setters)

		fake_frappe = ModuleType("frappe")
		fake_frappe._ = lambda text: text
		fake_frappe.throw = throw
		fake_frappe.clear_cache = lambda doctype: calls.append(("clear_cache", doctype))
		fake_frappe.get_cached_value = lambda doctype, name, field: (abbrs or {})[name]
		fake_frappe.db = SimpleNamespace(
			exists=exists,
			set_value=lambda doctype, name, values: calls.append(("set_value", name, values)),
		)
		fake_utils = ModuleType("frappe.utils")
		fake_utils.getdate = lambda value: datetime.date.fromisoformat(value)
		fake_property_setter = ModuleType("frappe.custom.doctype.property_setter.property_setter")
		fake_property_setter.make_property_setter = lambda *args, **kwargs: calls.append(
			("make", args, kwargs)
		)
		fake_naming = ModuleType("frappe.model.naming")
		fake_naming.make_autoname = lambda key: calls.append(("autoname", key)) or key.replace(".##", "01")
		modules = {
			"frappe": fake_frappe,
			"frappe.utils": fake_utils,
			"frappe.model": ModuleType("frappe.model"),
			"frappe.model.naming": fake_naming,
			"frappe.custom": ModuleType("frappe.custom"),
			"frappe.custom.doctype": ModuleType("frappe.custom.doctype"),
			"frappe.custom.doctype.property_setter": ModuleType("frappe.custom.doctype.property_setter"),
			"frappe.custom.doctype.property_setter.property_setter": fake_property_setter,
		}
		for name, module in modules.items():
			monkeypatch.setitem(sys.modules, name, module)

		importlib.reload(importlib.import_module("reyal_core.naming"))
		return importlib.reload(importlib.import_module(module_name)), calls

	return load
