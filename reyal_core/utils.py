import frappe


def get_display_name(user: str | None) -> str:
	"""Return the formatted display name for a user based on Reyal Settings."""
	if not user:
		return ""

	u = frappe.db.get_value(
		"User", user, ["first_name", "middle_name", "last_name", "full_name", "custom_short_name"], as_dict=True
	)
	if not u:
		return user

	fmt = _get_format()

	if fmt == "First + Middle Initial + Last Initial":
		return _first_middle_last_initial(u.first_name, u.middle_name, u.last_name) or u.full_name or user

	return _first_last_initial(u.first_name, u.last_name) or u.full_name or user


def compute_short_name_value(
	first_name: str | None,
	last_name: str | None,
	middle_name: str | None = None,
) -> str:
	"""Return formatted short name given raw name parts."""
	fmt = _get_format()

	if fmt == "First + Middle Initial + Last Initial":
		return _first_middle_last_initial(first_name, middle_name, last_name)

	return _first_last_initial(first_name, last_name)


def _get_format() -> str:
	try:
		return frappe.db.get_single_value("Reyal Settings", "user_short_display_name_format") or "First + Last Initial"
	except Exception:
		return "First + Last Initial"


def _first_last_initial(first_name: str | None, last_name: str | None) -> str:
	first = (first_name or "").strip()
	last = (last_name or "").strip()
	if first and last:
		return f"{first} {last[0]}."
	return first or last


def _first_middle_last_initial(
	first_name: str | None, middle_name: str | None, last_name: str | None
) -> str:
	first = (first_name or "").strip()
	middle = (middle_name or "").strip()
	last = (last_name or "").strip()
	parts = [first]
	if middle:
		parts.append(f"{middle[0]}.")
	if last:
		parts.append(f"{last[0]}.")
	return " ".join(filter(None, parts))
