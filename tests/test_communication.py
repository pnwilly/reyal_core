import importlib
import re
import sys
from types import ModuleType, SimpleNamespace


class FakeDoc(dict):
	def __getattr__(self, name):
		return self.get(name)

	def set_onload(self, key, value):
		self.setdefault("__onload", {})[key] = value


USERS = [
	{"name": "jane@reyal.biz", "full_name": "Jane Wanjiru Doe", "custom_short_name": "Jane D."},
	{"name": "Patrick@reyal.biz", "full_name": "Patrick Otieno", "custom_short_name": None},
	{"name": "Administrator", "full_name": "Administrator", "custom_short_name": "Admin"},
]

CONTACT_EMAILS = [
	{"parent": "Amara", "email_id": "amara@northwind.example"},
	{"parent": "Amara", "email_id": "amara.o@northwind.example"},
	{"parent": "Patrick Willy", "email_id": "Patrick@reyal.biz"},
	{"parent": "Unlinked", "email_id": "unlinked@example.com"},
]


def load_communication(monkeypatch):
	calls = []

	def get_all(doctype, filters, fields, order_by=None):
		calls.append((doctype, filters))
		names = filters.get("name", filters.get("parent"))[1]
		rows = USERS if doctype == "User" else CONTACT_EMAILS
		key = "name" if doctype == "User" else "parent"
		return [SimpleNamespace(**row) for row in rows if row[key] in names]

	fake_utils = ModuleType("frappe.utils")
	fake_utils.split_emails = lambda text: [part.strip() for part in text.split(",") if part.strip()]
	fake_utils.extract_email_id = lambda text: (re.search(r"<([^>]+)>", text) or [None, text])[1].strip()
	titles = {("Project", "PROJ-0001"): "Fleet Tyre Rollout 2027", ("Customer", "Acme"): "Acme"}
	title_fields = {"Project": "project_name", "Customer": "customer_name", "User": None}
	fake_frappe = ModuleType("frappe")
	fake_frappe.get_all = get_all
	fake_frappe.get_meta = lambda doctype: SimpleNamespace(title_field=title_fields.get(doctype))
	fake_frappe.db = SimpleNamespace(get_value=lambda doctype, name, field: titles.get((doctype, name)))
	fake_frappe.utils = fake_utils
	monkeypatch.setitem(sys.modules, "frappe", fake_frappe)
	monkeypatch.setitem(sys.modules, "frappe.utils", fake_utils)

	import reyal_core.communication as communication

	return importlib.reload(communication), calls


def link(doctype, name):
	return FakeDoc(link_doctype=doctype, link_name=name)


def test_addressed_contacts_match_linked_contacts_by_address(monkeypatch):
	communication, calls = load_communication(monkeypatch)
	doc = FakeDoc(
		sender="Amara Okafor <AMARA@northwind.example>",
		recipients="patrick@reyal.biz, unlinked@example.com",
		timeline_links=[link("Contact", "Amara"), link("Contact", "Patrick Willy"), link("Supplier", "S1")],
	)

	assert communication.get_addressed_contacts(doc) == {
		"amara@northwind.example": "Amara",
		"patrick@reyal.biz": "Patrick Willy",
	}
	assert calls[0][1]["parent"] == ("in", ["Amara", "Patrick Willy"])


def test_addressed_contacts_skip_the_query_without_linked_contacts(monkeypatch):
	communication, calls = load_communication(monkeypatch)
	doc = FakeDoc(sender="amara@northwind.example", timeline_links=[link("Supplier", "S1")])

	assert communication.get_addressed_contacts(doc) == {}
	assert calls == []


def test_short_names_cover_the_reference_and_timeline_users(monkeypatch):
	communication, calls = load_communication(monkeypatch)
	doc = FakeDoc(
		reference_doctype="User",
		reference_name="Administrator",
		timeline_links=[
			link("User", "jane@reyal.biz"),
			link("User", "Patrick@reyal.biz"),
			link("Supplier", "Acme"),
		],
	)

	assert communication.get_short_names(doc) == {
		"administrator": "Admin",
		"jane@reyal.biz": "Jane D.",
		"patrick@reyal.biz": "Patrick Otieno",
	}
	assert calls[0][1] == {"name": ("in", ["Administrator", "Patrick@reyal.biz", "jane@reyal.biz"])}


def test_short_names_ignore_addresses(monkeypatch):
	communication, calls = load_communication(monkeypatch)
	doc = FakeDoc(sender="jane@reyal.biz", recipients="Administrator")

	assert communication.get_short_names(doc) == {}
	assert calls == []


def test_onload_sends_names_only_for_email(monkeypatch):
	communication, _ = load_communication(monkeypatch)
	links = [link("Contact", "Amara")]
	email = FakeDoc(
		communication_medium="Email",
		sender="amara@northwind.example",
		reference_doctype="User",
		reference_name="jane@reyal.biz",
		timeline_links=links,
	)
	phone = FakeDoc(communication_medium="Phone", sender="amara@northwind.example", timeline_links=links)
	communication.add_names(email)
	communication.add_names(phone)

	assert email["__onload"] == {
		"contacts": {"amara@northwind.example": "Amara"},
		"short_names": {"jane@reyal.biz": "Jane D."},
		"reference_title": None,
	}
	assert "__onload" not in phone


def test_reference_title_only_when_it_differs_from_the_name(monkeypatch):
	communication, _ = load_communication(monkeypatch)

	assert communication.get_reference_title(
		FakeDoc(reference_doctype="Project", reference_name="PROJ-0001")
	) == ("Fleet Tyre Rollout 2027")
	assert (
		communication.get_reference_title(FakeDoc(reference_doctype="Customer", reference_name="Acme"))
		is None
	)
	assert (
		communication.get_reference_title(FakeDoc(reference_doctype="User", reference_name="jane@reyal.biz"))
		is None
	)
	assert communication.get_reference_title(FakeDoc()) is None
