import importlib
import sys
from types import SimpleNamespace


class FakeDB:
	def __init__(self, configured_format=None):
		self.configured_format = configured_format

	def get_single_value(self, doctype, fieldname):
		assert doctype == "Reyal Settings"
		assert fieldname == "user_short_display_name_format"
		return self.configured_format


def load_utils(monkeypatch, configured_format=None):
	fake_frappe = SimpleNamespace(db=FakeDB(configured_format))
	monkeypatch.setitem(sys.modules, "frappe", fake_frappe)

	import reyal_core.utils as utils

	return importlib.reload(utils)


def test_compute_short_name_defaults_to_first_last_initial(monkeypatch):
	utils = load_utils(monkeypatch)

	assert utils.compute_short_name_value("Ada", "Lovelace") == "Ada L."


def test_compute_short_name_can_include_middle_initial(monkeypatch):
	utils = load_utils(monkeypatch, "First + Middle Initial + Last Initial")

	assert utils.compute_short_name_value("Ada", "Lovelace", "Byron") == "Ada B. L."


def test_compute_short_name_handles_missing_parts(monkeypatch):
	utils = load_utils(monkeypatch)

	assert utils.compute_short_name_value("Ada", None) == "Ada"
	assert utils.compute_short_name_value(None, "Lovelace") == "Lovelace"
