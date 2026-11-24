import pytest
from conftest import ValidationError

PAYMENT_OPTIONS = "PMT-.POSTYY.POSTMM.#\nTRF-.POSTYY.POSTMM.#"
STOCK_OPTIONS = (
	"SE-.POSTYY.POSTMM.#\nST-.POSTYY.POSTMM.#\nMI-.POSTYY.POSTMM.#\nMR-.POSTYY.POSTMM.#\nSTM-.POSTYY.POSTMM.#"
)


class FakeMeta:
	def __init__(self, fields=(), options="", autoname=None):
		self.fields, self.options, self.autoname = set(fields), options, autoname

	def has_field(self, fieldname):
		return fieldname in self.fields

	def get_options(self, fieldname):
		return self.options


class FakeDoc(dict):
	def __init__(self, doctype, meta, previous=None, new=False, **values):
		super().__init__(values)
		self.doctype, self.meta, self.previous, self.new = doctype, meta, previous, new
		self.docstatus = values.get("docstatus", 0)

	__getattr__ = dict.get

	def __setattr__(self, key, value):
		if key in ("doctype", "meta", "previous", "new", "docstatus"):
			object.__setattr__(self, key, value)
		else:
			self[key] = value

	def is_new(self):
		return self.new

	def get_doc_before_save(self):
		return self.previous


def payment(payment_type="Pay", **values):
	return FakeDoc(
		"Payment Entry", FakeMeta({"naming_series"}, PAYMENT_OPTIONS), payment_type=payment_type, **values
	)


@pytest.fixture
def drafts(load_with_fake_frappe, monkeypatch):
	module, _ = load_with_fake_frappe("reyal_core.drafts")
	renames = []
	monkeypatch.setattr(module, "get_prefix", lambda series, doc: f"{series.split('-')[0]}-{doc['period']}")
	monkeypatch.setattr(module, "rename_draft", lambda *args: renames.append(args))
	module.renames = renames
	return module


@pytest.mark.parametrize(
	("payment_type", "series"), [("Internal Transfer", "TRF-"), ("Pay", "PMT-"), ("Receive", "PMT-")]
)
def test_payment_takes_the_series_for_its_type(drafts, payment_type, series):
	doc = payment(payment_type, naming_series="PMT-.POSTYY.POSTMM.#")
	drafts.set_draft_series(doc)

	assert doc.naming_series == f"{series}.POSTYY.POSTMM.#"


def stock_entry(stock_entry_type, **values):
	return FakeDoc(
		"Stock Entry", FakeMeta({"naming_series"}, STOCK_OPTIONS), stock_entry_type=stock_entry_type, **values
	)


@pytest.mark.parametrize(
	("purpose", "series"),
	[
		("Material Transfer", "ST-"),
		("Material Issue", "MI-"),
		("Material Receipt", "MR-"),
		("Manufacture", "SE-"),
		("Material Transfer for Manufacture", "STM-"),
	],
)
def test_stock_entry_takes_the_series_for_the_purpose_of_its_type(drafts, monkeypatch, purpose, series):
	monkeypatch.setattr(drafts.frappe, "get_cached_value", lambda doctype, name, field: purpose)
	doc = stock_entry("Site Issue", naming_series="SE-.POSTYY.POSTMM.#")
	drafts.set_draft_series(doc)

	assert doc.naming_series == f"{series}.POSTYY.POSTMM.#"


def test_stock_entry_draft_switched_to_issue_takes_the_issue_series(drafts, monkeypatch):
	monkeypatch.setattr(drafts.frappe, "get_cached_value", lambda doctype, name, field: name)
	previous = stock_entry("Material Transfer", naming_series="ST-.POSTYY.POSTMM.#", period="2503")
	doc = stock_entry("Material Issue", name="ST-25031", naming_series="ST-.POSTYY.POSTMM.#", period="2503")
	doc.previous = previous
	drafts.keep_draft_name_current(doc)

	assert doc.naming_series == "MI-.POSTYY.POSTMM.#"
	assert drafts.renames == [(doc, "MI-.POSTYY.POSTMM.#", "ST-.POSTYY.POSTMM.#", previous)]


@pytest.mark.parametrize(
	("doctype", "options", "is_return", "series"),
	[
		("Purchase Invoice", "Bill-RET-.POSTYY.POSTMM.#\nBill-.POSTYY.POSTMM.#", 0, "Bill-.POSTYY.POSTMM.#"),
		(
			"Purchase Invoice",
			"Bill-.POSTYY.POSTMM.#\nBill-RET-.POSTYY.POSTMM.#",
			1,
			"Bill-RET-.POSTYY.POSTMM.#",
		),
		("Purchase Receipt", "GR-.POSTYY.POSTMM.#\nGR-RET-.POSTYY.POSTMM.#", 1, "GR-RET-.POSTYY.POSTMM.#"),
		("Delivery Note", "DN-.POSTYY.POSTMM.#\nDN-RET-.POSTYY.POSTMM.#", 1, "DN-RET-.POSTYY.POSTMM.#"),
		("Delivery Note", "DN-.POSTYY.POSTMM.#\nDN-RET-.POSTYY.POSTMM.#", 0, "DN-.POSTYY.POSTMM.#"),
	],
)
def test_return_takes_the_return_series(drafts, doctype, options, is_return, series):
	doc = FakeDoc(doctype, FakeMeta({"naming_series"}, options), is_return=is_return)
	drafts.set_draft_series(doc)

	assert doc.naming_series == series


INVOICE_OPTIONS = "INV-.YY.MM.#\nRINV-.YY.MM.#"


def invoice(is_return=0, **values):
	return FakeDoc(
		"Sales Invoice", FakeMeta({"naming_series"}, INVOICE_OPTIONS), is_return=is_return, **values
	)


@pytest.mark.parametrize(("is_return", "series"), [(0, "INV-.YY.MM.#"), (1, "RINV-.YY.MM.#")])
def test_sales_invoice_takes_rinv_for_a_return_whatever_series_was_picked(drafts, is_return, series):
	doc = invoice(is_return, naming_series="RINV-.YY.MM.#" if not is_return else "INV-.YY.MM.#", new=True)
	drafts.set_draft_series(doc)

	assert doc.naming_series == series


def test_sales_invoice_draft_switched_to_return_stops_the_save(drafts):
	doc = invoice(1, name="INV-2611390", naming_series="INV-.YY.MM.#")

	with pytest.raises(ValidationError):
		drafts.check_invoice_series(doc)


@pytest.mark.parametrize("changes", [{"new": True}, {"docstatus": 1}, {"is_return": 0}])
def test_new_submitted_or_matching_sales_invoices_pass(drafts, changes):
	doc = invoice(1, name="INV-2611390", naming_series="INV-.YY.MM.#")
	for key, value in changes.items():
		setattr(doc, key, value)
	drafts.check_invoice_series(doc)


def test_other_doctypes_use_their_series_field_or_naming(drafts):
	journal = FakeDoc("Journal Entry", FakeMeta({"naming_series"}), naming_series="JE-.POSTYY.POSTMM.##")
	transfer = FakeDoc("Share Transfer", FakeMeta(autoname="SHT-.DATEYY.DATEMM.#"))
	unnamed = FakeDoc("Note", FakeMeta(autoname="hash"))

	assert drafts.series_for(journal) == "JE-.POSTYY.POSTMM.##"
	assert drafts.series_for(transfer) == "SHT-.DATEYY.DATEMM.#"
	assert drafts.series_for(unnamed) is None


def test_draft_on_a_retired_series_moves_to_the_current_one(drafts):
	options = "JE-.POSTYY.POSTMM.##"
	previous = FakeDoc("Journal Entry", FakeMeta({"naming_series"}, options), naming_series="JE-.YY.MM.##")
	doc = FakeDoc(
		"Journal Entry",
		FakeMeta({"naming_series"}, options),
		name="JE-261119",
		naming_series="JE-.YY.MM.##",
		period="2607",
	)
	doc.previous = previous
	drafts.keep_draft_name_current(doc)

	assert doc.naming_series == "JE-.POSTYY.POSTMM.##"
	assert drafts.renames == [(doc, "JE-.POSTYY.POSTMM.##", "JE-.YY.MM.##", previous)]


def test_draft_moved_to_another_period_is_renamed(drafts):
	previous = payment(naming_series="PMT-.POSTYY.POSTMM.#", period="2610")
	doc = payment(name="PMT-26101", naming_series="PMT-.POSTYY.POSTMM.#", period="2611", previous=None)
	doc.previous = previous
	drafts.keep_draft_name_current(doc)

	assert drafts.renames == [(doc, "PMT-.POSTYY.POSTMM.#", "PMT-.POSTYY.POSTMM.#", previous)]


def test_draft_switched_to_transfer_takes_the_transfer_series(drafts):
	previous = payment(naming_series="PMT-.POSTYY.POSTMM.#", period="2610")
	doc = payment("Internal Transfer", name="PMT-26101", naming_series="PMT-.POSTYY.POSTMM.#", period="2610")
	doc.previous = previous
	drafts.keep_draft_name_current(doc)

	assert (doc.naming_series, previous.naming_series) == ("TRF-.POSTYY.POSTMM.#", "TRF-.POSTYY.POSTMM.#")
	assert drafts.renames == [(doc, "TRF-.POSTYY.POSTMM.#", "PMT-.POSTYY.POSTMM.#", previous)]


@pytest.mark.parametrize(
	"changes",
	[{"new": True}, {"docstatus": 1}, {"amended_from": "PMT-26101"}, {"period": "2610"}],
)
def test_new_submitted_amended_or_matching_documents_keep_their_name(drafts, changes):
	doc = payment(name="PMT-26101", naming_series="PMT-.POSTYY.POSTMM.#", period="2611")
	for key, value in changes.items():
		setattr(doc, key, value)
	drafts.keep_draft_name_current(doc)

	assert drafts.renames == []


def test_missing_typed_series_stops_the_save(drafts):
	doc = FakeDoc("Payment Entry", FakeMeta({"naming_series"}, "ACC-PAY-.YYYY.-"), payment_type="Pay")

	with pytest.raises(ValidationError):
		drafts.typed_series(doc)
