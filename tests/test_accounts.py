import pytest
from conftest import ValidationError


def test_posting_date_sets_the_year_and_month(load_with_fake_frappe):
	naming, _ = load_with_fake_frappe("reyal_core.naming")
	journal = {"posting_date": "2024-07-25"}

	assert (naming.posting_year(journal, "POSTYY"), naming.posting_month(journal, "POSTMM")) == ("24", "07")


def test_transaction_date_sets_the_year_and_month(load_with_fake_frappe):
	naming, _ = load_with_fake_frappe("reyal_core.naming")
	order = {"transaction_date": "2026-11-05"}

	year = naming.transaction_year(order, "TRANSYY")
	month = naming.transaction_month(order, "TRANSMM")

	assert (year, month) == ("26", "11")


def test_posting_date_is_required(load_with_fake_frappe):
	naming, _ = load_with_fake_frappe("reyal_core.naming")

	with pytest.raises(ValidationError):
		naming.posting_year({"posting_date": None})


def test_accounting_series_are_offered_with_the_first_as_default(load_with_fake_frappe):
	accounts, calls = load_with_fake_frappe(
		"reyal_core.accounts",
		(
			"Journal Entry",
			"Payment Entry",
			"Purchase Invoice",
			"Purchase Receipt",
			"Sales Order",
			"Stock Entry",
		),
	)
	accounts.set_accounting_naming()

	assert [call[1][:4] for call in calls if call[0] == "make"] == [
		("Journal Entry", "naming_series", "options", "JE-.POSTYY.POSTMM.##"),
		("Journal Entry", "naming_series", "default", "JE-.POSTYY.POSTMM.##"),
		("Payment Entry", "naming_series", "options", "PMT-.POSTYY.POSTMM.#\nTRF-.POSTYY.POSTMM.#"),
		("Payment Entry", "naming_series", "default", "PMT-.POSTYY.POSTMM.#"),
		("Purchase Invoice", "naming_series", "options", "Bill-.POSTYY.POSTMM.#\nBill-RET-.POSTYY.POSTMM.#"),
		("Purchase Invoice", "naming_series", "default", "Bill-.POSTYY.POSTMM.#"),
		("Purchase Receipt", "naming_series", "options", "GR-.POSTYY.POSTMM.#\nGR-RET-.POSTYY.POSTMM.#"),
		("Purchase Receipt", "naming_series", "default", "GR-.POSTYY.POSTMM.#"),
		("Sales Order", "naming_series", "options", "SO-.TRANSYY.TRANSMM.#"),
		("Sales Order", "naming_series", "default", "SO-.TRANSYY.TRANSMM.#"),
		(
			"Stock Entry",
			"naming_series",
			"options",
			"SE-.POSTYY.POSTMM.#\nST-.POSTYY.POSTMM.#\nMI-.POSTYY.POSTMM.#\nMR-.POSTYY.POSTMM.#\nSTM-.POSTYY.POSTMM.#",
		),
		("Stock Entry", "naming_series", "default", "SE-.POSTYY.POSTMM.#"),
	]


def test_accounting_naming_is_skipped_without_erpnext(load_with_fake_frappe):
	accounts, calls = load_with_fake_frappe("reyal_core.accounts")
	accounts.set_accounting_naming()

	assert calls == []
