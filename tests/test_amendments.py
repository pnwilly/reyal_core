import importlib
import sys
from types import SimpleNamespace


class Flags(dict):
	__getattr__ = dict.get
	__setattr__ = dict.__setitem__


def get_setting(enabled):
	"""Fake frappe.db.get_single_value for the Reyal Settings switch."""

	def get_single_value(doctype, fieldname):
		assert (doctype, fieldname) == ("Reyal Settings", "allow_deleting_amended_originals")
		return int(enabled)

	return get_single_value


def make_doc(docstatus, has_amended_from=True):
	return SimpleNamespace(
		doctype="Purchase Invoice",
		name="Bill-1",
		flags=Flags(),
		docstatus=SimpleNamespace(is_cancelled=lambda: docstatus == 2),
		meta=SimpleNamespace(has_field=lambda fieldname: has_amended_from),
	)


def load_amendments(monkeypatch, has_amendments=True, enabled=True):
	db = SimpleNamespace(
		exists=lambda doctype, filters: has_amendments, get_single_value=get_setting(enabled)
	)
	monkeypatch.setitem(sys.modules, "frappe", SimpleNamespace(db=db))

	import reyal_core.amendments as amendments

	return importlib.reload(amendments)


def test_deleting_an_amended_original_keeps_its_series_number(monkeypatch):
	amendments = load_amendments(monkeypatch)
	doc = make_doc(docstatus=2)

	amendments.keep_series_of_amended_original(doc)

	assert doc.flags.reyal_keep_naming_series is True


def test_series_number_is_released_while_the_setting_is_off(monkeypatch):
	amendments = load_amendments(monkeypatch, enabled=False)
	doc = make_doc(docstatus=2)

	amendments.keep_series_of_amended_original(doc)

	assert doc.flags.reyal_keep_naming_series is None


def test_cancelled_documents_without_amendments_release_their_number(monkeypatch):
	amendments = load_amendments(monkeypatch, has_amendments=False)
	doc = make_doc(docstatus=2)

	amendments.keep_series_of_amended_original(doc)

	assert doc.flags.reyal_keep_naming_series is None


def test_documents_that_are_not_cancelled_are_ignored(monkeypatch):
	amendments = load_amendments(monkeypatch)
	doc = make_doc(docstatus=0)

	amendments.keep_series_of_amended_original(doc)

	assert doc.flags.reyal_keep_naming_series is None


def test_doctypes_without_amendments_are_ignored(monkeypatch):
	amendments = load_amendments(monkeypatch)
	doc = make_doc(docstatus=2, has_amended_from=False)

	amendments.keep_series_of_amended_original(doc)

	assert doc.flags.reyal_keep_naming_series is None


AMENDMENT = {"doc": "Bill-1", "reference_doctype": "Purchase Invoice", "reference_docname": "Bill-1-1"}
PAYMENT = {"doc": "Bill-1", "reference_doctype": "Payment Entry", "reference_docname": "PE-1"}
MISSING_SOURCE = ("amended_from", "Bill-1", "Could not find Amended From: Bill-1")
MISSING_SUPPLIER = ("supplier", "Gone", "Could not find Supplier: Gone")
CANCELLED_LINK = ("project", "P-1", "Cannot link cancelled document: P-1")


class FakeDocument:
	"""Like Frappe, rewrites each link from the database, blanking ones whose target is gone."""

	def __init__(self, amended_from=None):
		self.amended_from = amended_from

	def get(self, fieldname):
		return getattr(self, fieldname, None)

	def set(self, fieldname, value):
		setattr(self, fieldname, value)

	def get_invalid_links(self, is_submittable=False):
		invalid_links = [MISSING_SUPPLIER]
		if self.amended_from:
			self.amended_from = None
			invalid_links.insert(0, MISSING_SOURCE)
		return invalid_links, [CANCELLED_LINK]


def load_patched_delete(monkeypatch, enabled=True):
	"""Install fake Frappe modules, apply the patch, and return the patched delete module."""
	reverted = []
	delete_doc = SimpleNamespace(
		get_linked_docs=lambda doc, method="Delete", limit=None: [AMENDMENT, PAYMENT],
		update_naming_series=lambda doc: reverted.append(doc.name),
		reverted=reverted,
	)
	linked_with = SimpleNamespace(get_statically_linked_docs=delete_doc.get_linked_docs)
	document = SimpleNamespace(Document=type("Document", (FakeDocument,), {}))
	model = SimpleNamespace(delete_doc=delete_doc, document=document)
	form = SimpleNamespace(linked_with=linked_with)
	desk = SimpleNamespace(form=form)
	fake_frappe = SimpleNamespace(
		model=model,
		desk=desk,
		db=SimpleNamespace(get_single_value=get_setting(enabled)),
		get_meta=lambda doctype: SimpleNamespace(has_field=lambda fieldname: doctype == "Purchase Invoice"),
		get_all=lambda doctype, filters, pluck: ["Bill-1-1"] if filters == {"amended_from": "Bill-1"} else [],
	)
	modules = {
		"frappe": fake_frappe,
		"frappe.model": model,
		"frappe.model.delete_doc": delete_doc,
		"frappe.model.document": document,
		"frappe.desk": desk,
		"frappe.desk.form": form,
		"frappe.desk.form.linked_with": linked_with,
	}
	for name, module in modules.items():
		monkeypatch.setitem(sys.modules, name, module)

	import reyal_core.amendments as amendments

	importlib.reload(amendments).patch_amended_deletion()
	return delete_doc, linked_with, document.Document


def test_amendments_do_not_block_deleting_their_cancelled_original(monkeypatch):
	delete_doc, linked_with, _ = load_patched_delete(monkeypatch)
	original = SimpleNamespace(doctype="Purchase Invoice", name="Bill-1")

	assert delete_doc.get_linked_docs(original, "Delete") == [PAYMENT]
	assert linked_with.get_statically_linked_docs(original, method="Delete", limit=5) == [PAYMENT]


def test_amendments_block_deletion_while_the_setting_is_off(monkeypatch):
	delete_doc, _, _ = load_patched_delete(monkeypatch, enabled=False)
	original = SimpleNamespace(doctype="Purchase Invoice", name="Bill-1")

	assert delete_doc.get_linked_docs(original, "Delete") == [AMENDMENT, PAYMENT]


def test_amendments_still_count_when_cancelling(monkeypatch):
	delete_doc, _, _ = load_patched_delete(monkeypatch)
	original = SimpleNamespace(doctype="Purchase Invoice", name="Bill-1")

	assert delete_doc.get_linked_docs(original, "Cancel") == [AMENDMENT, PAYMENT]


def test_deleted_amended_original_keeps_its_series_number(monkeypatch):
	delete_doc, _, _ = load_patched_delete(monkeypatch)
	amended = SimpleNamespace(name="Bill-1", flags=Flags(reyal_keep_naming_series=True))
	plain = SimpleNamespace(name="Bill-2", flags=Flags())

	delete_doc.update_naming_series(amended)
	delete_doc.update_naming_series(plain)

	assert delete_doc.reverted == ["Bill-2"]


def test_amendment_of_a_deleted_original_still_validates(monkeypatch):
	_, _, document_class = load_patched_delete(monkeypatch)

	amendment = document_class(amended_from="Bill-1")

	invalid_links, cancelled_links = amendment.get_invalid_links(is_submittable=True)

	assert invalid_links == [MISSING_SUPPLIER]
	assert cancelled_links == [CANCELLED_LINK]
	assert amendment.amended_from == "Bill-1"


def test_amendment_of_a_deleted_original_saves_after_the_setting_is_turned_off(monkeypatch):
	_, _, document_class = load_patched_delete(monkeypatch, enabled=False)
	amendment = document_class(amended_from="Bill-1")

	assert amendment.get_invalid_links()[0] == [MISSING_SUPPLIER]
	assert amendment.amended_from == "Bill-1"


def test_documents_without_amended_from_validate_as_before(monkeypatch):
	_, _, document_class = load_patched_delete(monkeypatch)
	document = document_class()

	assert document.get_invalid_links() == ([MISSING_SUPPLIER], [CANCELLED_LINK])
	assert document.amended_from is None


def test_patch_amended_deletion_applies_once(monkeypatch):
	delete_doc, _, document_class = load_patched_delete(monkeypatch)
	patched = delete_doc.get_linked_docs, delete_doc.update_naming_series, document_class.get_invalid_links

	import reyal_core.amendments as amendments

	amendments.patch_amended_deletion()

	assert (
		delete_doc.get_linked_docs,
		delete_doc.update_naming_series,
		document_class.get_invalid_links,
	) == (patched)
