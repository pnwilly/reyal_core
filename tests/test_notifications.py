import importlib
import sys
from types import SimpleNamespace

import pytest


class PermissionErrorForTest(Exception):
	pass


class FakeDB:
	def __init__(self):
		self.rows = [
			{"name": "read-current", "for_user": "reader@example.com", "read": 1, "modified": 2},
			{"name": "unread-current", "for_user": "reader@example.com", "read": 0, "modified": 3},
			{"name": "read-other", "for_user": "other@example.com", "read": 1, "modified": 1},
		]
		self.deleted_filters = []

	def delete(self, doctype, filters):
		assert doctype == "Notification Log"
		self.deleted_filters.append(filters)

	def exists(self, doctype, filters):
		assert doctype == "Notification Log"
		for row in self.rows:
			if all(row.get(key) == value for key, value in filters.items()):
				return row["name"]
		return None


def load_notifications(monkeypatch, fake_db=None, user="reader@example.com", read_only=False):
	fake_db = fake_db or FakeDB()
	fake_frappe = SimpleNamespace(
		PermissionError=PermissionErrorForTest,
		_=lambda message: message,
		db=fake_db,
		flags=SimpleNamespace(read_only=read_only),
		get_all=lambda doctype, **kwargs: get_all(fake_db, doctype, **kwargs),
		session=SimpleNamespace(user=user),
		throw=lambda message, exc: (_ for _ in ()).throw(exc(message)),
		whitelist=lambda func=None, **kwargs: func if func is not None else lambda wrapped: wrapped,
	)
	monkeypatch.setitem(sys.modules, "frappe", fake_frappe)

	import reyal_core.notifications as notifications

	return importlib.reload(notifications), fake_db


def get_all(fake_db, doctype, filters, fields, order_by, limit, pluck):
	assert doctype == "Notification Log"
	assert fields == ["name"]
	assert order_by == "modified desc"
	assert pluck == "name"

	rows = [
		row
		for row in fake_db.rows
		if row["for_user"] == filters["for_user"] and row["read"] == filters["read"]
	]
	rows.sort(key=lambda row: row["modified"], reverse=True)
	return [row["name"] for row in rows[:limit]]


def test_sanitize_limit_bounds_values(monkeypatch):
	notifications, _fake_db = load_notifications(monkeypatch)

	assert notifications._sanitize_limit("not a number") == 200
	assert notifications._sanitize_limit(0) == 1
	assert notifications._sanitize_limit(900) == 500


def test_delete_read_notifications_only_targets_current_user_read_rows(monkeypatch):
	notifications, fake_db = load_notifications(monkeypatch)

	result = notifications.delete_read_notifications(limit=10)

	assert result == {"deleted": 1}
	assert fake_db.deleted_filters == [{"name": ["in", ["read-current"]]}]


def test_delete_notification_requires_current_user_ownership(monkeypatch):
	notifications, fake_db = load_notifications(monkeypatch)

	assert notifications.delete_notification("read-other") == {"deleted": 0}
	assert fake_db.deleted_filters == []

	assert notifications.delete_notification("read-current") == {"deleted": 1}
	assert fake_db.deleted_filters == [{"name": "read-current", "for_user": "reader@example.com"}]


def test_guest_cannot_delete_notifications(monkeypatch):
	notifications, _fake_db = load_notifications(monkeypatch, user="Guest")

	with pytest.raises(PermissionErrorForTest):
		notifications.delete_notification("read-current")
