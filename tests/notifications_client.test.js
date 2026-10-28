const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const test = require("node:test");

test("sidebar setup patches the V16 notification view", () => {
	const events = {};
	const empty = {
		length: 0,
		remove() { return this; },
		find() { return this; },
		filter() { return this; },
		each() { return this; },
		get() { return null; },
		on(name, handler) { events[name] = handler; return this; },
	};
	const view = { container: empty, render_notifications_dropdown() {} };
	const original = view.render_notifications_dropdown;
	const context = {
		document: {},
		$: () => empty,
		frappe: {
			boot: { desk_settings: { notifications: true } },
			ui: {},
			app: { sidebar: { notifications: { tabs: { notifications: view } } } },
		},
	};
	const source = fs.readFileSync(path.join(__dirname,
		"../reyal_core/public/js/notification_row_delete_v5.js"), "utf8");
	vm.runInNewContext(source, context);
	assert.equal(typeof events.sidebar_setup, "function");
	events.sidebar_setup();
	assert.notEqual(view.render_notifications_dropdown, original);
});
