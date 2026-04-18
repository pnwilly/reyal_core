import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


_CUSTOM_FIELDS = {
	"User": [
		{
			"fieldname": "custom_short_name",
			"fieldtype": "Data",
			"label": "Short Name",
			"insert_after": "full_name",
			"read_only": 1,
			"no_copy": 1,
			"description": "Set by Reyal Settings",
		}
	]
}


def after_install():
	create_custom_fields(_CUSTOM_FIELDS, ignore_validate=True, update=True)
	_backfill_short_names()
	frappe.db.commit()


def _backfill_short_names():
	"""Compute short_name for all existing users after install."""
	from reyal_core.utils import compute_short_name_value

	users = frappe.db.get_all("User", filters={"user_type": "System User"}, fields=["name", "first_name", "middle_name", "last_name"])
	for u in users:
		short_name = compute_short_name_value(u.first_name, u.last_name, u.get("middle_name"))
		frappe.db.set_value("User", u.name, "custom_short_name", short_name, update_modified=False)
