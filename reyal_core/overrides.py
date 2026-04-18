"""Monkey-patches for Frappe utility functions.

Applied once per worker process via the before_request hook.
Both patches replace full_name with custom_short_name wherever available,
falling back gracefully to the original behaviour when not set.
"""

import frappe


def apply_patches():
	"""Apply all reyal_core patches. Safe to call repeatedly — patches only once."""
	import frappe.utils as fu
	import frappe.desk.search as fs

	if getattr(fu, "_reyal_core_patched", False):
		return

	fu._original_get_fullname = fu.get_fullname
	fu._original_add_user_info = fu.add_user_info
	fu.get_fullname = _get_fullname
	fu.add_user_info = _add_user_info

	fs._original_get_users_for_mentions = fs.get_users_for_mentions
	fs.get_users_for_mentions = _get_users_for_mentions

	fu._reyal_core_patched = True


# -- Patched implementations

def _get_fullname(user=None):
	"""Return custom_short_name when set, otherwise fall back to full_name."""
	if not user:
		user = frappe.session.user

	if not hasattr(frappe.local, "fullnames"):
		frappe.local.fullnames = {}

	if not frappe.local.fullnames.get(user):
		row = frappe.db.get_value(
			"User", user, ["first_name", "last_name", "full_name", "custom_short_name"], as_dict=True
		)
		if row:
			frappe.local.fullnames[user] = (
				row.custom_short_name
				or row.full_name
				or " ".join(filter(None, [row.first_name, row.last_name]))
				or user
			)
		else:
			frappe.local.fullnames[user] = user

	return frappe.local.fullnames.get(user)


def _add_user_info(user, user_info):
	"""Populate user_info dict using custom_short_name as fullname when available."""
	if not user:
		return

	if isinstance(user, str):
		user = [user]

	missing_users = [u for u in user if u not in user_info]
	if not missing_users:
		return

	missing_info = frappe.get_all(
		"User",
		{"name": ("in", missing_users)},
		["full_name", "custom_short_name", "user_image", "name", "email", "time_zone"],
	)

	for info in missing_info:
		display = info.custom_short_name or info.full_name or info.name
		user_info.setdefault(info.name, frappe._dict()).update(
			fullname=display,
			image=info.user_image,
			name=info.name,
			email=info.email,
			time_zone=info.time_zone,
		)


def _get_users_for_mentions():
	"""Return mention-autocomplete list using custom_short_name when available."""
	rows = frappe.get_all(
		"User",
		fields=["name as id", "full_name", "custom_short_name"],
		filters={
			"name": ["not in", ("Administrator", "Guest")],
			"allowed_in_mentions": True,
			"user_type": "System User",
			"enabled": True,
		},
	)
	for row in rows:
		row["value"] = row.custom_short_name or row.full_name or row.id
	return rows
