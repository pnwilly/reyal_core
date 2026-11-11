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

function chain(overrides = {}) {
	const proxy = new Proxy(overrides, {
		get(target, prop) {
			if (prop in target) return target[prop];
			if (prop === "length") return 0;
			return () => proxy;
		},
	});
	return proxy;
}

function make_row(name, classes) {
	const handlers = {};
	const attrs = { "data-name": name };
	const row = chain({
		classes: new Set(classes),
		handlers,
		attr(key, value) {
			if (value === undefined) return attrs[key];
			attrs[key] = value;
			return row;
		},
		hasClass: (cls) => row.classes.has(cls),
		removeClass(cls) { row.classes.delete(cls); return row; },
		on(event, handler) { handlers[event] = handler; return row; },
		closest: () => ({ is: () => true }),
	});
	return row;
}

function make_view(rows, unread_count, badge) {
	const container = chain({
		length: 1,
		find: () => chain({
			filter(fn) {
				const matched = rows.filter((row) => fn.call(row));
				const collection = chain({
					each(cb) { matched.forEach((row) => cb.call(row)); return collection; },
					removeClass(cls) { matched.forEach((row) => row.removeClass(cls)); return collection; },
				});
				return collection;
			},
		}),
	});
	return {
		container,
		unread_count,
		dropdown_items: rows.map((row) => ({ name: row.attr("data-name"), read: row.hasClass("unread") ? 0 : 1 })),
		render_notifications_dropdown() {},
		update_count_badge(count) { badge.push(count); },
	};
}

const MARK_READ = "frappe.desk.doctype.notification_log.notification_log.mark_as_read";

function load_panels(sidebar_rows, popover_rows = null, server_count = 2) {
	const calls = [];
	const badge = [];
	const all_rows = [...sidebar_rows, ...(popover_rows || [])];
	const sidebar = make_view(sidebar_rows, 3, badge);
	class Notifications {
		make_tab_view(item) { this.tabs = { [item.id]: this.view }; }
	}
	const context = {
		document: chain(),
		$: (target) => {
			if (typeof target === "function") return target();
			return all_rows.includes(target) ? target : chain();
		},
		frappe: {
			boot: { desk_settings: { notifications: true }, notification_unread_count: 3 },
			session: { user: "test@example.com" },
			ui: { Notifications },
			app: { sidebar: { notifications: { tabs: { notifications: sidebar } } } },
			xcall: (method, args) => {
				calls.push([method, args]);
				return Promise.resolve(method === MARK_READ ? null : server_count);
			},
		},
		__: (text) => text,
	};
	const source = fs.readFileSync(path.join(__dirname,
		"../reyal_core/public/js/notification_row_delete_v5.js"), "utf8");
	vm.runInNewContext(source, context);

	let popover = null;
	if (popover_rows) {
		const instance = new Notifications();
		instance.view = popover = make_view(popover_rows, 3, badge);
		instance.make_tab_view({ id: "notifications" });
	}
	return { calls, badge, sidebar, popover, boot: context.frappe.boot };
}

const settle = () => new Promise((resolve) => setImmediate(resolve));

test("opening an unread notification marks only that log read", async () => {
	const unread = make_row("LOG-1", ["unread"]);
	const { calls, badge, sidebar, boot } = load_panels([unread]);

	unread.handlers["click.reyal_mark_read"]();
	await settle();

	assert.equal(unread.hasClass("unread"), false);
	assert.equal(JSON.stringify(calls), JSON.stringify([
		[MARK_READ, { docname: "LOG-1" }],
		["frappe.client.get_count", { doctype: "Notification Log", filters: { for_user: "test@example.com", read: 0 } }],
	]));
	assert.equal(sidebar.dropdown_items[0].read, 1);
	assert.equal(boot.notification_unread_count, 2);
	assert.deepEqual(badge, [2]);
});

test("opening a read notification does not call the server", async () => {
	const read = make_row("LOG-2", []);
	const { calls, badge } = load_panels([read]);

	read.handlers["click.reyal_mark_read"]();
	await settle();

	assert.equal(calls.length, 0);
	assert.deepEqual(badge, []);
});

test("marking read in the desktop popover syncs the sidebar panel and the server count", async () => {
	const sidebar_row = make_row("LOG-3", ["unread"]);
	const popover_row = make_row("LOG-3", ["unread"]);
	const { badge, sidebar, popover, boot } = load_panels([sidebar_row], [popover_row], 1);

	popover_row.handlers["click.reyal_mark_read"]();
	await settle();

	assert.equal(popover_row.hasClass("unread"), false);
	assert.equal(sidebar_row.hasClass("unread"), false);
	assert.equal(sidebar.dropdown_items[0].read, 1);
	assert.equal(popover.dropdown_items[0].read, 1);
	assert.equal(sidebar.unread_count, 1);
	assert.equal(popover.unread_count, 1);
	assert.equal(boot.notification_unread_count, 1);
	assert.deepEqual(badge, [1]);
});
