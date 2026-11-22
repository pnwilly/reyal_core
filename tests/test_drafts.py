import pytest
from conftest import ValidationError

PAYMENT_OPTIONS = "PMT-.POSTYY.POSTMM.#\nTRF-.POSTYY.POSTMM.#"


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


def test_missing_payment_series_stops_the_save(drafts):
	doc = FakeDoc("Payment Entry", FakeMeta({"naming_series"}, "ACC-PAY-.YYYY.-"), payment_type="Pay")

	with pytest.raises(ValidationError):
		drafts.payment_series(doc)
