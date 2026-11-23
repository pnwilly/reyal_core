import pytest
from conftest import ValidationError

ASSET_DOCTYPES = (
	"Asset",
	"Asset Capitalization",
	"Asset Repair",
	"Asset Movement",
	"Asset Value Adjustment",
)


def test_purchase_and_failure_dates_set_the_year_and_month(load_with_fake_frappe):
	assets, _ = load_with_fake_frappe("reyal_core.assets")
	van = {"purchase_date": "2026-07-04"}
	repair = {"failure_date": "2026-11-23"}

	assert (assets.purchase_year(van, "PURYY"), assets.purchase_month(van, "PURMM")) == ("26", "07")
	assert (assets.failure_year(repair, "FAILYY"), assets.failure_month(repair, "FAILMM")) == ("26", "11")


@pytest.mark.parametrize("variable", ["purchase_year", "failure_month"])
def test_asset_naming_date_is_required(load_with_fake_frappe, variable):
	assets, _ = load_with_fake_frappe("reyal_core.assets")

	with pytest.raises(ValidationError):
		getattr(assets, variable)({})


def test_asset_naming_is_created_and_owned_by_reyal(load_with_fake_frappe):
	assets, calls = load_with_fake_frappe("reyal_core.assets", ASSET_DOCTYPES)
	assets.set_asset_naming()

	assert [call[1][:4] for call in calls if call[0] == "make"] == [
		("Asset", "naming_series", "options", ".ABBR.-.PURYY.PURMM.#"),
		("Asset", "naming_series", "default", ".ABBR.-.PURYY.PURMM.#"),
		("Asset Capitalization", "naming_series", "options", "ASC-.POSTYY.POSTMM.#"),
		("Asset Capitalization", "naming_series", "default", "ASC-.POSTYY.POSTMM.#"),
		("Asset Repair", "naming_series", "options", "ASR-.FAILYY.FAILMM.#"),
		("Asset Repair", "naming_series", "default", "ASR-.FAILYY.FAILMM.#"),
		("Asset Movement", None, "autoname", "ASM-.TRANSYY.TRANSMM.#"),
		("Asset Value Adjustment", None, "autoname", "AVA-.DATEYY.DATEMM.#"),
	]


def test_asset_naming_is_skipped_without_erpnext(load_with_fake_frappe):
	assets, calls = load_with_fake_frappe("reyal_core.assets")
	assets.set_asset_naming()

	assert calls == []
