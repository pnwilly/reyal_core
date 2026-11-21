import pytest

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


def test_other_doctypes_use_their_series_field_or_naming(drafts):
	journal = FakeDoc("Journal Entry", FakeMeta({"naming_series"}), naming_series="JE-.POSTYY.POSTMM.##")
	transfer = FakeDoc("Share Transfer", FakeMeta(autoname="SHT-.DATEYY.DATEMM.#"))
	unnamed = FakeDoc("Note", FakeMeta(autoname="hash"))

	assert drafts.series_for(journal) == "JE-.POSTYY.POSTMM.##"
	assert drafts.series_for(transfer) == "SHT-.DATEYY.DATEMM.#"
	assert drafts.series_for(unnamed) is None


def test_draft_moved_to_another_period_is_renamed(drafts):
	previous = payment(naming_series="PMT-.POSTYY.POSTMM.#", period="2610")
	doc = payment(name="PMT-26101", naming_series="PMT-.POSTYY.POSTMM.#", period="2611", previous=None)
	doc.previous = previous
	drafts.keep_draft_name_current(doc)

	assert drafts.renames == [(doc, "PMT-.POSTYY.POSTMM.#", "PMT-.POSTYY.POSTMM.#", previous)]


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
