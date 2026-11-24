import pytest
from conftest import ValidationError

ACCOUNTING_DOCTYPES = {
	"Delivery Note": ("DN-.POSTYY.POSTMM.#", "DN-RET-.POSTYY.POSTMM.#"),
	"Journal Entry": ("JE-.POSTYY.POSTMM.##",),
	"Material Request": ("RQ-.TRANSYY.TRANSMM.#",),
	"Payment Entry": ("PMT-.POSTYY.POSTMM.#", "TRF-.POSTYY.POSTMM.#"),
	"Purchase Invoice": ("Bill-.POSTYY.POSTMM.#", "Bill-RET-.POSTYY.POSTMM.#"),
	"Purchase Order": ("PO-.TRANSYY.TRANSMM.#",),
	"Purchase Receipt": ("GR-.POSTYY.POSTMM.#", "GR-RET-.POSTYY.POSTMM.#"),
	"Quotation": ("QTN-.TRANSYY.TRANSMM.#",),
	"Sales Invoice": ("INV-.YY.MM.#", "RINV-.YY.MM.#"),
	"Sales Order": ("SO-.TRANSYY.TRANSMM.#",),
	"Stock Entry": (
		"SE-.POSTYY.POSTMM.#",
		"ST-.POSTYY.POSTMM.#",
		"MI-.POSTYY.POSTMM.#",
		"MR-.POSTYY.POSTMM.#",
		"STM-.POSTYY.POSTMM.#",
	),
	"Stock Reconciliation": ("SRE-.POSTYY.POSTMM.##",),
	"Supplier Quotation": ("SQ-.TRANSYY.TRANSMM.#",),
}


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
	accounts, calls = load_with_fake_frappe("reyal_core.accounts", tuple(ACCOUNTING_DOCTYPES))
	accounts.set_accounting_naming()

	offered = {}
	for call in calls:
		if call[0] == "make":
			doctype, _field, property_name, value = call[1][:4]
			offered.setdefault(doctype, {})[property_name] = value

	assert offered == {
		doctype: {"options": "\n".join(series), "default": series[0]}
		for doctype, series in ACCOUNTING_DOCTYPES.items()
	}


def test_accounting_naming_is_skipped_without_erpnext(load_with_fake_frappe):
	accounts, calls = load_with_fake_frappe("reyal_core.accounts")
	accounts.set_accounting_naming()

	assert calls == []
