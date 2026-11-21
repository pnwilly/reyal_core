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
		("Shareholder", "naming_series", "options", "SH-.ABBR.-.#"),
		("Shareholder", "naming_series", "default", "SH-.ABBR.-.#"),
	]
	assert [call[1] for call in calls if call[0] == "set_value"] == [
		"Share Transfer-main-autoname",
		"Shareholder-naming_series-options",
		"Shareholder-naming_series-default",
	]


def test_share_naming_is_skipped_without_erpnext(load_with_fake_frappe):
	shares, calls = load_with_fake_frappe("reyal_core.shares")
	shares.set_share_naming()

	assert calls == []
