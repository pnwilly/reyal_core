(() => {
	const { Toolbar } = frappe.ui.form;
	const set_primary_action = Toolbar.prototype.set_primary_action;

	/** Replace Frappe's disabled "Already amended" button with a link to the amendment. */
	Toolbar.prototype.set_primary_action = function (dirty) {
		if (this.get_action_status() !== "Amend") return set_primary_action.call(this, dirty);
		if (!dirty) this.page.clear_user_actions();

		const { doctype, name } = this.frm.doc;
		// POST: the GET response is browser-cached for 10 minutes and would hide a new amendment.
		frappe
			.xcall("frappe.client.is_document_amended", { doctype, docname: name }, "POST")
			.then((amendment) => {
				if (this.frm.doc.name !== name) return;
				if (!amendment) return this.set_page_actions("Amend");
				this.page.clear_actions();
				this.page.set_primary_action(__("View Amendment"), () =>
					frappe.set_route("Form", doctype, amendment)
				);
			});
	};
})();
