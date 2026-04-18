import frappe


def compute_short_name(doc, method=None):
	"""Recompute custom_short_name on the User document after every save."""
	if doc.user_type != "System User":
		return

	from reyal_core.utils import compute_short_name_value

	short_name = compute_short_name_value(doc.first_name, doc.last_name, doc.get("middle_name"))
	frappe.db.set_value("User", doc.name, "custom_short_name", short_name, update_modified=False)
