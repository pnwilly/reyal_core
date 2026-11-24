// ERPNext shows the Series field on every new document, which overrides a Series field hidden
// through Customize Form or reyal_core's naming. Leave a hidden Series field hidden.
(() => {
	const toggle = window.erpnext && erpnext.toggle_naming_series;
	if (!toggle) return;

	erpnext.toggle_naming_series = function (...args) {
		const doctype = window.cur_frm && cur_frm.doctype;
		const series = doctype && frappe.meta.get_docfield(doctype, "naming_series");
		if (series && series.hidden) return;
		return toggle.apply(this, args);
	};
})();
