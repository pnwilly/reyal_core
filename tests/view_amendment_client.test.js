const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const test = require("node:test");

function load(amendment) {
	class Toolbar {
		set_primary_action(dirty) {
			this.original_called_with = dirty;
		}
		set_page_actions(status) {
			this.page.primary = status;
		}
	}
	const calls = [];
	const routes = [];
	const context = {
		__: (text) => text,
		frappe: {
			ui: { form: { Toolbar } },
			xcall: (...args) => {
				calls.push(args);
				return Promise.resolve(amendment);
			},
			set_route: (...args) => routes.push(args),
		},
	};
	const source = fs.readFileSync(
		path.join(__dirname, "../reyal_core/public/js/view_amendment.js"),
		"utf8"
	);
	vm.runInNewContext(source, context);
	return { Toolbar, calls, routes };
}

function make_toolbar(Toolbar, status) {
	const page = {
		clear_user_actions() {
			this.user_actions_cleared = true;
		},
		clear_actions() {
			this.primary = null;
		},
		set_primary_action(label, click) {
			this.primary = label;
			this.click = click;
		},
	};
	const frm = { doc: { doctype: "Purchase Invoice", name: "Bill-1" } };
	return Object.assign(new Toolbar(), { page, frm, get_action_status: () => status });
}

test("amended cancelled document offers View Amendment", async () => {
	const { Toolbar, calls, routes } = load("Bill-1-1");
	const toolbar = make_toolbar(Toolbar, "Amend");
	toolbar.set_primary_action(false);
	await new Promise(setImmediate);
	assert.deepEqual(JSON.parse(JSON.stringify(calls[0].slice(0, 2))), [
		"frappe.client.is_document_amended",
		{ doctype: "Purchase Invoice", docname: "Bill-1" },
	]);
	assert.equal(toolbar.page.primary, "View Amendment");
	toolbar.page.click();
	assert.deepEqual(JSON.parse(JSON.stringify(routes)), [["Form", "Purchase Invoice", "Bill-1-1"]]);
});

test("lookup avoids the browser-cached GET so a new amendment shows at once", () => {
	const { Toolbar, calls } = load("Bill-1-1");
	make_toolbar(Toolbar, "Amend").set_primary_action(false);
	const [, , type, opts] = calls[0];
	assert.equal(type, "POST");
	assert.ok(!opts || !opts.cache);
});

test("cancelled document without an amendment keeps Amend", async () => {
	const { Toolbar } = load(null);
	const toolbar = make_toolbar(Toolbar, "Amend");
	toolbar.set_primary_action(false);
	await new Promise(setImmediate);
	assert.equal(toolbar.page.primary, "Amend");
});

test("result is ignored after the form moves to another document", async () => {
	const { Toolbar } = load("Bill-1-1");
	const toolbar = make_toolbar(Toolbar, "Amend");
	toolbar.set_primary_action(false);
	toolbar.frm.doc = { doctype: "Purchase Invoice", name: "Bill-9" };
	await new Promise(setImmediate);
	assert.equal(toolbar.page.primary, undefined);
});

test("other statuses use Frappe's own primary action", () => {
	const { Toolbar, calls } = load("Bill-1-1");
	const toolbar = make_toolbar(Toolbar, "Submit");
	toolbar.set_primary_action(true);
	assert.equal(toolbar.original_called_with, true);
	assert.equal(calls.length, 0);
});
