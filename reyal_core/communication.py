import frappe
from frappe.utils import extract_email_id, split_emails


def add_names(doc, method=None):
	"""Send the names an email form shows: addressed contacts, linked users and the reference title."""
	if doc.communication_medium != "Email":
		return
	doc.set_onload("contacts", get_addressed_contacts(doc))
	doc.set_onload("short_names", get_short_names(doc))
	doc.set_onload("reference_title", get_reference_title(doc))


def get_addressed_contacts(doc) -> dict[str, str]:
	"""Map each lowercased address on the From, To, Cc and Bcc lines to its linked Contact."""
	emails = get_addressed_emails(doc)
	contacts = get_linked_names(doc, "Contact")
	if not emails or not contacts:
		return {}

	rows = frappe.get_all(
		"Contact Email",
		filters={"parenttype": "Contact", "parent": ("in", sorted(contacts))},
		fields=["parent", "email_id"],
		order_by="parent asc",
	)
	matches = {}
	for row in rows:
		email = (row.email_id or "").lower()
		if email in emails:
			matches.setdefault(email, row.parent)
	return matches


def get_reference_title(doc) -> str | None:
	"""The reference document's title, when its doctype has a title field that differs from the name."""
	if not doc.reference_doctype or not doc.reference_name:
		return None
	title_field = frappe.get_meta(doc.reference_doctype).title_field
	if not title_field:
		return None
	title = frappe.db.get_value(doc.reference_doctype, doc.reference_name, title_field)
	return title if title and title != doc.reference_name else None


def get_short_names(doc) -> dict[str, str]:
	"""Map the lowercased ID of each linked user to their short name."""
	user_ids = get_linked_names(doc, "User")
	if not user_ids:
		return {}

	users = frappe.get_all(
		"User",
		filters={"name": ("in", sorted(user_ids))},
		fields=["name", "full_name", "custom_short_name"],
	)
	return {
		user.name.lower(): user.custom_short_name or user.full_name
		for user in users
		if user.custom_short_name or user.full_name
	}


def get_addressed_emails(doc) -> set[str]:
	"""Lowercased emails on the From, To, Cc and Bcc lines."""
	addresses = [doc.sender or ""]
	for field in ("recipients", "cc", "bcc"):
		addresses.extend(split_emails(doc.get(field) or ""))
	emails = {extract_email_id(address).lower() for address in addresses if address}
	emails.discard("")
	return emails


def get_linked_names(doc, doctype: str) -> set[str]:
	"""Documents of one type the email links to, as its reference or a timeline link."""
	links = [(doc.reference_doctype, doc.reference_name)]
	links.extend((row.link_doctype, row.link_name) for row in doc.get("timeline_links") or [])
	return {name for link_doctype, name in links if link_doctype == doctype and name}
