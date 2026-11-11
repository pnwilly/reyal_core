import frappe


def keep_series_of_amended_original(doc, method=None):
	"""Keep the series number of a deleted cancelled document that has amendments.

	Frappe hands the newest number back on delete; a new document could then take it and
	collide with the surviving `-1` amendment when amended. amended_from is left as is, so
	amending an amendment still names the next one `-2`.
	"""
	if not doc.docstatus.is_cancelled() or not doc.meta.has_field("amended_from"):
		return
	if frappe.db.exists(doc.doctype, {"amended_from": doc.name}):
		doc.flags.reyal_keep_naming_series = True


def patch_amended_deletion():
	"""Let a cancelled document be deleted while its amendments remain, once per process."""
	import frappe.desk.form.linked_with as linked_with
	import frappe.model.delete_doc as delete_doc
	from frappe.model.document import Document

	if getattr(delete_doc.get_linked_docs, "ignores_amendments", False):
		return

	delete_doc.get_linked_docs = skip_amendments(delete_doc.get_linked_docs)
	if hasattr(linked_with, "get_statically_linked_docs"):
		linked_with.get_statically_linked_docs = delete_doc.get_linked_docs
	delete_doc.update_naming_series = skip_flagged_series(delete_doc.update_naming_series)
	Document.get_invalid_links = allow_deleted_amendment_source(Document.get_invalid_links)


def skip_amendments(get_linked_docs):
	"""Leave amendments out of Delete blockers, as Frappe already does for Cancel.

	Frappe V16's Delete lists blockers and deletes them first, so the amendment would go too.
	"""

	def get_linked_docs_except_amendments(doc, method="Delete", *args, **kwargs):
		links = get_linked_docs(doc, method, *args, **kwargs)
		if method != "Delete" or not links:
			return links

		amendments = get_amendments(doc.doctype, doc.name)
		return [
			link for link in links if (link["reference_doctype"], link["reference_docname"]) not in amendments
		]

	get_linked_docs_except_amendments.ignores_amendments = True
	return get_linked_docs_except_amendments


def skip_flagged_series(update_naming_series):
	"""Skip the series revert for documents flagged by keep_series_of_amended_original."""

	def update_naming_series_unless_flagged(doc):
		if not doc.flags.get("reyal_keep_naming_series"):
			update_naming_series(doc)

	return update_naming_series_unless_flagged


def allow_deleted_amendment_source(get_invalid_links):
	"""Accept an amended_from that points to a deleted document.

	Frappe already ignores amended_from in its cancelled-link check; without this, saving an
	amendment of a deleted original (for example on repost) fails with "Could not find". Frappe
	also rewrites each link from the database, which blanks one whose target is gone, so the
	original value is put back.
	"""

	def get_invalid_links_except_amended_from(self, *args, **kwargs):
		amended_from = self.get("amended_from")
		invalid_links, cancelled_links = get_invalid_links(self, *args, **kwargs)
		if amended_from and not self.get("amended_from"):
			self.set("amended_from", amended_from)
		return [link for link in invalid_links if link[0] != "amended_from"], cancelled_links

	return get_invalid_links_except_amended_from


def get_amendments(doctype, name):
	"""(doctype, name) pairs of the documents amended from the given one."""
	if not frappe.get_meta(doctype).has_field("amended_from"):
		return set()

	return {
		(doctype, amendment)
		for amendment in frappe.get_all(doctype, filters={"amended_from": name}, pluck="name")
	}
