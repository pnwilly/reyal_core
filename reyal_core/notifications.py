import frappe
from frappe import _


@frappe.whitelist()
def delete_read_notifications(limit: int = 200) -> dict[str, int]:
	"""Delete read notification logs for the current session user.

	Only notifications owned by the logged-in user are deleted.
	Returns the number of deleted rows.
	"""
	if frappe.session.user == "Guest":
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	if frappe.flags.read_only:
		return {"deleted": 0}

	delete_limit = _sanitize_limit(limit)
	docnames = frappe.get_all(
		"Notification Log",
		filters={"for_user": frappe.session.user, "read": 1},
		fields=["name"],
		order_by="modified desc",
		limit=delete_limit,
		pluck="name",
	)

	if not docnames:
		return {"deleted": 0}

	frappe.db.delete("Notification Log", {"name": ["in", docnames]})
	return {"deleted": len(docnames)}


@frappe.whitelist()
def delete_notification(docname: str) -> dict[str, int]:
	"""Delete one notification log for the current session user."""
	if frappe.session.user == "Guest":
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	if frappe.flags.read_only or not docname:
		return {"deleted": 0}

	filters = {"name": str(docname)}
	if frappe.session.user != "Administrator":
		filters["for_user"] = frappe.session.user

	owned_doc = frappe.db.exists("Notification Log", filters)
	if not owned_doc:
		return {"deleted": 0}

	frappe.db.delete("Notification Log", {"name": owned_doc})
	return {"deleted": 1}


def _sanitize_limit(limit: int) -> int:
	try:
		value = int(limit)
	except Exception:
		value = 200

	return max(1, min(value, 500))
