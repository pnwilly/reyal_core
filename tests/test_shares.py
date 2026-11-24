import pytest
from conftest import ValidationError

SHARE_DOCTYPES = ("Share Transfer", "Shareholder")


def test_date_sets_the_year_and_month(load_with_fake_frappe):
	naming, _ = load_with_fake_frappe("reyal_core.naming")
	transfer = {"date": "2024-07-25"}

	assert (naming.date_year(transfer, "DATEYY"), naming.date_month(transfer, "DATEMM")) == ("24", "07")


def test_company_sets_the_abbreviation(load_with_fake_frappe):
	naming, _ = load_with_fake_frappe("reyal_core.naming", abbrs={"OPERO CONSULTANCY SERVICES LTD": "OCS"})

	assert naming.company_abbr({"company": "OPERO CONSULTANCY SERVICES LTD"}, "ABBR") == "OCS"


@pytest.mark.parametrize(("variable", "doc"), [("date_year", {}), ("date_month", None), ("company_abbr", {})])
def test_naming_value_is_required(load_with_fake_frappe, variable, doc):
	naming, _ = load_with_fake_frappe("reyal_core.naming")

	with pytest.raises(ValidationError):
		getattr(naming, variable)(doc)


def test_share_naming_is_created_and_owned_by_reyal(load_with_fake_frappe):
	shares, calls = load_with_fake_frappe("reyal_core.shares", SHARE_DOCTYPES)
	shares.set_share_naming()

	assert [call[1][:4] for call in calls if call[0] == "make"] == [
		("Share Transfer", None, "autoname", "SHT-.DATEYY.DATEMM.#"),
		("Share Transfer", "from_folio_no", "fetch_if_empty", "1"),
		("Share Transfer", "to_folio_no", "fetch_if_empty", "1"),
		("Shareholder", "naming_series", "options", "SH-.ABBR.-.#"),
		("Shareholder", "naming_series", "default", "SH-.ABBR.-.#"),
		("Shareholder", "naming_series", "hidden", "1"),
	]
	assert [call[1] for call in calls if call[0] == "set_value"] == [
		"Share Transfer-main-autoname",
		"Share Transfer-from_folio_no-fetch_if_empty",
		"Share Transfer-to_folio_no-fetch_if_empty",
		"Shareholder-naming_series-options",
		"Shareholder-naming_series-default",
		"Shareholder-naming_series-hidden",
	]


class FakeShareholder:
	def __init__(self):
		self.folio_no = None
		self.saved = False

	def save(self):
		self.saved = True


@pytest.mark.parametrize("is_company", [False, True])
def test_new_folio_is_numbered_fn_with_two_digits(load_with_fake_frappe, is_company):
	shares, calls = load_with_fake_frappe("reyal_core.shares")
	holders = {"person": FakeShareholder(), "company": FakeShareholder()}
	transfer = type(
		"Transfer",
		(shares.ShareTransferFolio,),
		{
			"get_shareholder_doc": lambda self, name: holders["person"],
			"get_company_shareholder": lambda self: holders["company"],
		},
	)()

	folio = transfer.autoname_folio("person", is_company=is_company)
	holder = holders["company" if is_company else "person"]

	assert (folio, holder.folio_no, holder.saved) == ("FN01", "FN01", True)
	assert calls == [("autoname", "FN.##")]


def test_share_naming_is_skipped_without_erpnext(load_with_fake_frappe):
	shares, calls = load_with_fake_frappe("reyal_core.shares")
	shares.set_share_naming()

	assert calls == []
