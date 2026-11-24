const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const test = require("node:test");

const source = fs.readFileSync(path.join(__dirname, "../reyal_core/public/js/series_field.js"), "utf8");

function load(hidden) {
	const shown = [];
	const context = {
		cur_frm: { doctype: "Stock Entry" },
		frappe: { meta: { get_docfield: () => ({ fieldname: "naming_series", hidden }) } },
		erpnext: { toggle_naming_series: () => shown.push(true) },
	};
	context.window = context;
	vm.runInNewContext(source, context);
	context.erpnext.toggle_naming_series();
	return shown;
}

test("a hidden Series field stays hidden on new documents", () => {
	assert.deepEqual(load(1), []);
});

test("a visible Series field keeps ERPNext's behaviour", () => {
	assert.deepEqual(load(0), [true]);
});

test("sites without ERPNext load the file without errors", () => {
	const context = { frappe: {} };
	context.window = context;
	vm.runInNewContext(source, context);
	assert.equal(context.erpnext, undefined);
});
