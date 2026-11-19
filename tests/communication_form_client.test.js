const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const test = require("node:test");

// Same mapping as frappe.utils.escape_html.
const HTML_ESCAPES = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;", "`": "&#x60;", "=": "&#x3D;" };
const escape_html = (text) => String(text).replace(/[&<>"'`=]/g, (char) => HTML_ESCAPES[char]);

/** Text without tags; repeated so a tag split across another tag cannot survive. */
function text_of(html) {
	let text = html;
	let previous;
	do {
		previous = text;
		text = text.replace(/<[^>]*>/g, "");
	} while (text !== previous);
	return text;
}

/** The text of each Linked to row, one per document type. */
function link_rows(html) {
	return [...html.matchAll(/<div class="reyal-email-link-group">(.*?)<\/div>/g)].map((match) =>
		text_of(match[1]).replace(/\s+/g, " ").trim()
	);
}

/** An empty jQuery set: every call chains and does nothing. */
function empty_jquery() {
	const set = { length: 0, hasClass: () => false };
	set.children = () => set;
	for (const method of ["toggleClass", "removeClass", "addClass", "find", "remove", "after", "on", "attr", "text", "first"]) set[method] = () => set;
	return set;
}

function load() {
	const handlers = {};
	const context = {
		$: (target) => target?.$fake || empty_jquery(),
		__: (text, args) => (args ? text.replace("{0}", args[0]) : text),
		frappe: {
			provide(name) {
				name.split(".").reduce((parent, key) => (parent[key] ||= {}), context);
			},
			ui: { form: { on: (doctype, events) => (handlers[doctype] = events) } },
			utils: {
				escape_html,
				split_emails: (text) => (text ? text.split(",").map((part) => part.trim()) : []),
				get_form_link: (doctype, name) => `/desk/${doctype}/${name}`,
			},
			avatar: (user) => `<avatar user="${user}">`,
			// Frappe sets the title through setAttribute, so it arrives escaped.
			get_avatar: (css_class, title) => `<avatar title="${escape_html(title)}">`,
			datetime: {
				get_user_date_fmt: () => "dd-mm-yyyy",
				get_user_time_fmt: () => "HH:mm:ss",
				convert_to_user_tz: (value) => ({ format: (pattern) => `${value} as ${pattern}` }),
				prettyDate: (date, mini) => (mini ? context.age ?? "2 h" : "2 hours ago"),
			},
		},
	};
	const source = fs.readFileSync(
		path.join(__dirname, "../reyal_core/public/js/communication_form.js"),
		"utf8"
	);
	context.setInterval = () => {};
	vm.runInNewContext(source, context);
	return { communication: context.reyal_core.communication, handlers, context };
}

test("only saved emails use the email view", () => {
	const { communication } = load();
	const frm = (is_new, communication_medium) => ({
		is_new: () => is_new,
		doc: { communication_medium },
	});

	assert.equal(communication.is_email_view(frm(false, "Email")), true);
	assert.equal(communication.is_email_view(frm(true, "Email")), false);
	assert.equal(communication.is_email_view(frm(false, "Phone")), false);
});

test("header shows sender, recipients and date; the subject has its own pinned line", () => {
	const { communication } = load();
	const html = communication.header_html({
		subject: "Invoice overdue",
		sender: "jane@example.com",
		sender_full_name: "Jane Doe",
		recipients: "a@example.com, b@example.com",
		cc: "c@example.com",
		communication_date: "2026-11-19 10:00:00",
	});

	assert.doesNotMatch(html, /Invoice overdue/);
	assert.equal(
		communication.subject_html({ subject: "Invoice overdue" }),
		'<div class="reyal-email-subject">Invoice overdue</div>'
	);
	assert.match(html, /Jane Doe/);
	assert.match(html, /&lt;jane@example.com&gt;/);
	assert.match(html, /To<\/span><span class="reyal-email-value">a@example.com, b@example.com/);
	assert.match(html, /Cc<\/span><span class="reyal-email-value">c@example.com/);
	assert.doesNotMatch(html, /Bcc/);
	assert.match(html, /2026-11-19 10:00:00 as DD-MM-YYYY HH:mm\s*</);
	assert.match(html, /data-timestamp="2026-11-19 10:00:00"/);
	assert.match(html, />2 h ago</);
});

test("header escapes email fields", () => {
	const { communication } = load();
	const doc = {
		subject: "<img src=x onerror=alert(1)>",
		sender: "<b>@example.com",
		recipients: "<script>@example.com",
	};
	const html = communication.header_html(doc) + communication.subject_html(doc);

	assert.doesNotMatch(html, /<img|<script|<b>/i);
	assert.match(html, /&lt;img src&#x3D;x/);
});

test("system user sender uses their user avatar", () => {
	const { communication } = load();

	assert.match(communication.sender_html({ user: "jane@example.com" }).avatar, /user="jane@example.com"/);
	assert.match(communication.sender_html({ sender: "x@example.com" }).avatar, /title="x@example.com"/);
});

test("missing subject and sender fall back to labels", () => {
	const { communication } = load();
	const html = communication.header_html({});

	assert.match(communication.subject_html({}), /\(No subject\)/);
	assert.match(html, /Unknown sender/);
});

test("chips show failed delivery and read receipt, not direction", () => {
	const { communication } = load();
	const html = communication.chips_html({
		sent_or_received: "Sent",
		delivery_status: "Bounced",
		read_by_recipient: 1,
		read_by_recipient_on: "2026-11-19 11:00:00",
	});

	assert.doesNotMatch(html, /Sent</);
	assert.match(html, /red reyal-email-chip">Bounced</);
	assert.match(html, />Read 2026-11-19 11:00:00 as DD-MM-YYYY HH:mm</);
});

test("chips leave status and direction to the title bar and skip ordinary delivery", () => {
	const { communication } = load();

	assert.equal(communication.chips_html({ status: "Open", sent_or_received: "Sent", delivery_status: "Sent" }), "");
});

test("links show the reference and other timeline links once", () => {
	const { communication } = load();
	const html = communication.links_html(
		{
			reference_doctype: "Purchase Invoice",
			reference_name: "Bill-1",
			timeline_links: [
				{ link_doctype: "Purchase Invoice", link_name: "Bill-1" },
				{ link_doctype: "Supplier", link_name: "S1", link_title: "Acme <Ltd>" },
			],
		},
		false
	);

	assert.match(html, /Linked to<\/span><span class="reyal-email-value"><div class="reyal-email-link-group"><span class="reyal-email-doctype">Purchase Invoice/);
	assert.match(html, /href="\/desk\/Purchase Invoice\/Bill-1">Bill-1</);
	assert.deepEqual(link_rows(html), ["Purchase Invoice Bill-1", "Supplier Acme &lt;Ltd&gt;"]);
	assert.equal(html.match(/Bill-1</g).length, 1);
	assert.doesNotMatch(html, /Also on/);
	assert.doesNotMatch(html, /reyal-email-edit-links/);
});

test("editors get a links line with Edit even without links", () => {
	const { communication } = load();
	const html = communication.links_html({}, true);

	assert.match(html, /reyal-email-value"><span class="text-muted">None<\/span> <a class="reyal-email-edit-links">Edit<\/a>/);
	assert.equal(communication.links_html({}, false), "");
});

test("details list only filled technical fields and escape the message id", () => {
	const { communication } = load();
	const html = communication.details_html({
		email_account: "Support",
		message_id: "<abc@mail>",
	});

	assert.match(html, /<summary>Details<\/summary>/);
	assert.match(html, /Email Account<\/dt><dd><a[^>]+>Support</);
	assert.match(html, /<code>&lt;abc@mail&gt;<\/code>/);
	assert.doesNotMatch(html, /In Reply To|Email Template|Send After/);
	assert.equal(communication.details_html({}), "");
});

test("refresh hides the stock sections only in the email view", () => {
	const { handlers } = load();
	const toggled = [];
	const frm = {
		is_new: () => false,
		doc: { communication_medium: "Phone" },
		wrapper: {},
		toggle_display: (fields, show) => toggled.push([fields, show]),
		page: { wrapper: {}, get_breadcrumbs: () => [] },
		layout: { wrapper: { find: () => ({ remove() {} }) } },
		fields_dict: {},
	};
	handlers.Communication.refresh.call(null, frm);

	assert.equal(toggled[0][1], true);
	assert.ok(toggled[0][0].includes("timeline_links_sections"));
});

test("email view drops the reference toolbar button that Linked to replaces", () => {
	const { communication } = load();
	const removed = [];
	const frm = {
		doc: { reference_doctype: "Purchase Invoice", reference_name: "Bill-1" },
		has_perm: () => false,
		remove_custom_button: (label) => removed.push(label),
		layout: {
			wrapper: {
				prepend(html) {
					(this.prepended ||= []).push(html);
					return this;
				},
			},
		},
		fields_dict: { content: { $wrapper: { closest: () => ({ after() {} }) } } },
	};
	communication.render(frm);

	assert.deepEqual(removed, ["Bill-1"]);
	assert.match(frm.layout.wrapper.prepended[1], /^<div class="reyal-email-subject">/);
});

function page_with(crumb) {
	const page = {
		title: "Invoice overdue",
		breadcrumbs: [{ label: "Communication", href: "/desk/communication" }, crumb],
		get_breadcrumbs: () => page.breadcrumbs,
		set_breadcrumbs: (items) => (page.breadcrumbs = items),
	};
	return page;
}

test("title crumb becomes a direction arrow with the subject as its tooltip", () => {
	const { communication } = load();
	const sent = page_with({ label: "Invoice overdue" });
	communication.set_direction(sent, "Sent");
	const received = page_with({ label: "Invoice overdue" });
	communication.set_direction(received, "Received");

	assert.deepEqual(
		{ ...sent.breadcrumbs[1] },
		{ title: "Sent: Invoice overdue", prefix: "arrow-up-right" }
	);
	assert.equal(received.breadcrumbs[1].prefix, "arrow-down-left");
	assert.equal(sent.breadcrumbs[0].href, "/desk/communication");
});

test("non-email records keep the stock title crumb", () => {
	const { communication } = load();
	const page = page_with({ label: "Call log" });
	page.title = "Call log";
	communication.set_direction(page, null);

	assert.deepEqual({ ...page.breadcrumbs[1] }, { label: "Call log" });
});

test("list crumb is named after the medium and opens the filtered list", () => {
	const { communication } = load();
	const page = page_with({ label: "Invoice overdue" });
	communication.set_medium_crumb(page, "Email");

	assert.deepEqual(
		{ ...page.breadcrumbs[0] },
		{ label: "Email", href: "/desk/communication?communication_medium=Email" }
	);
	assert.equal(page.breadcrumbs[1].label, "Invoice overdue");
});

test("list crumb keeps Communication for Other, a missing medium or a hidden list", () => {
	const { communication } = load();
	for (const medium of ["Other", "", undefined]) {
		const page = page_with({ label: "Log" });
		communication.set_medium_crumb(page, medium);
		assert.equal(page.breadcrumbs[0].label, "Communication");
	}
	const title_only = { get_breadcrumbs: () => [{ label: "Log" }], set_breadcrumbs: assert.fail };
	communication.set_medium_crumb(title_only, "Email");
});

test("dates drop seconds and keep a minute-only format as is", () => {
	const { communication, context } = load();

	assert.equal(communication.datetime_to_user("2026-11-19 10:00:42"), "2026-11-19 10:00:42 as DD-MM-YYYY HH:mm");
	context.frappe.datetime.get_user_time_fmt = () => "HH:mm";
	assert.equal(communication.datetime_to_user("2026-11-19 10:00:42"), "2026-11-19 10:00:42 as DD-MM-YYYY HH:mm");
});

test("age reads like 8 h ago, but now stays now", () => {
	const { communication, context } = load();

	assert.equal(communication.age_text("2026-11-19 10:00:00"), "2 h ago");
	context.age = "now";
	assert.equal(communication.age_text("2026-11-19 10:00:00"), "now");
	context.age = "";
	assert.equal(communication.age_text("2099-01-01 00:00:00"), "");
});

test("each document type starts its own row, its documents comma-separated", () => {
	const { communication } = load();
	const html = communication.links_html(
		{
			timeline_links: [
				{ link_doctype: "Customer", link_name: "C1", link_title: "Northwind" },
				{ link_doctype: "Supplier", link_name: "S1", link_title: "Acme" },
				{ link_doctype: "Customer", link_name: "C2", link_title: "Hotel Cavallino" },
			],
		},
		false
	);

	assert.deepEqual(link_rows(html), ["Customer Northwind, Hotel Cavallino", "Supplier Acme"]);
	assert.equal(communication.link_groups([]).length, 0);
});

test("the reference leads and shares a row with documents of its type; Edit ends the last row", () => {
	const { communication } = load();
	const html = communication.links_html(
		{
			reference_doctype: "Customer",
			reference_name: "C1",
			timeline_links: [
				{ link_doctype: "Supplier", link_name: "S1", link_title: "Acme" },
				{ link_doctype: "Customer", link_name: "C2", link_title: "Hotel Cavallino" },
			],
		},
		true,
		{ reference_title: "Northwind" }
	);

	assert.deepEqual(link_rows(html), ["Customer Northwind, Hotel Cavallino", "Supplier Acme Edit"]);
	assert.equal(html.match(/Linked to/g).length, 1);
});

test("email contacts keep the stored name and addresses, not short names", () => {
	const { communication } = load();
	const short_names = { "jane@reyal.biz": "Jane D.", "patrick@reyal.biz": "Patrick O." };
	const html = communication.header_html(
		{
			sender: "jane@reyal.biz",
			sender_full_name: "Jane Wanjiru Doe",
			recipients: "patrick@reyal.biz, client@example.com",
		},
		{ short_names }
	);

	assert.match(html, /reyal-email-name">Jane Wanjiru Doe</);
	assert.match(html, /To<\/span><span class="reyal-email-value">patrick@reyal.biz, client@example.com/);
	assert.doesNotMatch(html, /Jane D\.|Patrick O\./);
});

test("without short names the sender falls back to the stored full name", () => {
	const { communication } = load();

	assert.equal(
		communication.sender_html({ sender: "x@example.com", sender_full_name: "Xavier Kim" }).name,
		"Xavier Kim"
	);
});

test("linked users show their Reyal short name", () => {
	const { communication } = load();
	const short_names = { administrator: "Admin", "jane@reyal.biz": "Jane D." };
	const html = communication.links_html(
		{
			reference_doctype: "User",
			reference_name: "Administrator",
			timeline_links: [
				{ link_doctype: "User", link_name: "jane@reyal.biz", link_title: "Jane Wanjiru Doe" },
				{ link_doctype: "Supplier", link_name: "jane@reyal.biz", link_title: "Jane Supplies" },
			],
		},
		false,
		{ short_names }
	);
	assert.deepEqual(link_rows(html), ["User Admin, Jane D.", "Supplier Jane Supplies"]);
});

test("timeline links read Linked to when there is no reference document", () => {
	const { communication } = load();
	const html = communication.links_html(
		{ timeline_links: [{ link_doctype: "Supplier", link_name: "S1" }] },
		false
	);

	assert.deepEqual(link_rows(html), ["Supplier S1"]);
});

test("addressed contacts show their saved name; no Contact appears under Linked to", () => {
	const { communication } = load();
	const doc = {
		sender: "amara@northwind.example",
		sender_full_name: "Amara Okafor",
		recipients: "Patrick@Reyal.biz, outsider@example.com",
		reference_doctype: "Supplier",
		reference_name: "S1",
		timeline_links: [
			{ link_doctype: "Contact", link_name: "Amara", link_title: "Amara" },
			{ link_doctype: "Contact", link_name: "Patrick Willy", link_title: "Patrick Willy" },
			{ link_doctype: "Contact", link_name: "Board", link_title: "Board <Members>" },
			{ link_doctype: "Customer", link_name: "C1", link_title: "Hotel Cavallino" },
		],
	};
	const contacts = { "amara@northwind.example": "Amara", "patrick@reyal.biz": "Patrick Willy" };
	const html = communication.header_html(doc, { contacts });
	const links = link_rows(communication.links_html(doc, false));

	assert.match(html, /reyal-email-name"><a class="reyal-email-link" href="\/desk\/Contact\/Amara" title="amara@northwind.example">Amara<\/a>/);
	assert.match(html, /title="Patrick@Reyal.biz">Patrick Willy<\/a>, outsider@example.com/);
	assert.doesNotMatch(html, /Amara Okafor/);
	assert.deepEqual(links, ["Supplier S1", "Customer Hotel Cavallino"]);
});

test("each header line keeps its value in its own column so wrapped lines indent", () => {
	const { communication } = load();

	assert.equal(
		communication.line_html("To", "a@example.com, b@example.com"),
		'<div class="reyal-email-line"><span class="reyal-email-label">To</span><span class="reyal-email-value">a@example.com, b@example.com</span></div>'
	);
});

function sidebar_frm({ title_row = true, date = "2026-11-19 10:00:00" } = {}) {
	const state = {
		meta_classes: new Set(),
		wrapper_classes: new Set(),
		inserted: [],
		removed: 0,
		title: "Quarterly supplier review",
		copy: "Quarterly supplier review",
	};
	const title_element = {
		...empty_jquery(),
		length: title_row ? 1 : 0,
		attr: (name, value) => ((state.copy = value), title_element),
		find: () => ({ first: () => ({ text: (value) => (state.title = value) }) }),
	};
	const row = { ...empty_jquery(), length: 1, first: () => row, after: (html) => state.inserted.push(html) };
	const meta = {
		...empty_jquery(),
		hasClass: (name) => state.meta_classes.has(name),
		children: (selector) => (selector === ".flex" ? row : empty_jquery()),
		removeClass: (name) => (state.meta_classes.delete(name), meta),
		toggleClass: (name, on) => (on ? state.meta_classes.add(name) : state.meta_classes.delete(name), meta),
		find: (selector) =>
			selector === ".form-title-text" ? title_element : { ...empty_jquery(), remove: () => state.removed++ },
	};
	const wrapper = {
		...empty_jquery(),
		toggleClass: (name, on) => (on ? state.wrapper_classes.add(name) : state.wrapper_classes.delete(name), wrapper),
	};
	const frm = {
		doc: { name: "059sgpupe4", communication_date: date },
		get_title: () => "Quarterly supplier review",
		wrapper: { $fake: wrapper },
		page: { sidebar: { $fake: { ...empty_jquery(), find: () => meta } } },
	};
	return { frm, state };
}

test("sidebar title row shows the ID, with the date below it", () => {
	const { communication } = load();
	const { frm, state } = sidebar_frm();
	communication.set_sidebar_details(frm, true);

	assert.equal(state.title, "059sgpupe4");
	assert.equal(state.copy, "059sgpupe4");
	assert.ok(state.meta_classes.has("reyal-email-meta"));
	assert.equal(state.inserted.length, 1);
	assert.match(state.inserted[0], /^<div class="reyal-email-sidebar-date"><div class="reyal-email-date">2026-11-19 10:00:00 as DD-MM-YYYY HH:mm/);
	assert.match(state.inserted[0], />2 h ago</);
	assert.ok(state.wrapper_classes.has("reyal-email-date-in-sidebar"));
	assert.equal(state.removed, 1);
});

test("without a sidebar title row the card keeps its date", () => {
	const { communication } = load();
	const { frm, state } = sidebar_frm({ title_row: false });
	communication.set_sidebar_details(frm, true);

	assert.ok(!state.meta_classes.has("reyal-email-meta"));
	assert.equal(state.inserted.length, 0);
	assert.ok(!state.wrapper_classes.has("reyal-email-date-in-sidebar"));
});

test("a record that stops being an email gets its stock title back", () => {
	const { communication } = load();
	const { frm, state } = sidebar_frm();
	communication.set_sidebar_details(frm, true);
	communication.set_sidebar_details(frm, false);

	assert.equal(state.title, "Quarterly supplier review");
	assert.equal(state.copy, "Quarterly supplier review");
	assert.ok(!state.meta_classes.has("reyal-email-meta"));
	assert.ok(!state.wrapper_classes.has("reyal-email-date-in-sidebar"));
});

test("other records' sidebars are left untouched", () => {
	const { communication } = load();
	const { frm, state } = sidebar_frm();
	communication.set_sidebar_details(frm, false);

	assert.equal(state.title, "Quarterly supplier review");
	assert.equal(state.inserted.length, 0);
});

test("the reference shows its title when the server sends one", () => {
	const { communication } = load();
	const doc = { reference_doctype: "Project", reference_name: "PROJ-0001" };
	const html = communication.links_html(doc, false, { reference_title: "Fleet Tyre Rollout 2027" });

	assert.match(html, /href="\/desk\/Project\/PROJ-0001">Fleet Tyre Rollout 2027</);
	assert.match(communication.links_html(doc, false), />PROJ-0001</);
});

test("a type's documents sit in their own column so a wrapped list indents past the type", () => {
	const { communication } = load();
	const html = communication.links_html(
		{ timeline_links: [{ link_doctype: "Customer", link_name: "C1", link_title: "Northwind" }] },
		true
	);

	assert.match(
		html,
		/<div class="reyal-email-link-group"><span class="reyal-email-doctype">Customer<\/span> <span class="reyal-email-link-items"><a[^>]+>Northwind<\/a> <a class="reyal-email-edit-links">Edit<\/a><\/span><\/div>/
	);
});

test("Edit opens Timeline Links and a second click hides them again", () => {
	const { communication, context } = load();
	const scrolled = [];
	context.frappe.utils.scroll_to = (element) => scrolled.push(element);
	const df = { hidden: 1 };
	const collapsed = [];
	const frm = {
		get_docfield: () => df,
		toggle_display: (field, show) => (df.hidden = show ? 0 : 1),
		fields_dict: { timeline_links_sections: { wrapper: "section", collapse: (hide) => collapsed.push(hide) } },
	};

	communication.toggle_timeline_links(frm);
	assert.equal(df.hidden, 0);
	assert.deepEqual(collapsed, [false]);
	assert.deepEqual(scrolled, ["section"]);

	communication.toggle_timeline_links(frm);
	assert.equal(df.hidden, 1);
	assert.equal(scrolled.length, 1);
});

function folding_frm() {
	const handlers = {};
	const head = {
		off: (namespace) => {
			for (const key of Object.keys(handlers)) if (key.endsWith(namespace)) delete handlers[key];
			return head;
		},
		on: (events, handler) => {
			for (const event of events.split(" ")) handlers[event] = handler;
			return head;
		},
	};
	const state = { collapsed: false, hidden: 0 };
	const frm = {
		toggle_display: (field, show) => (state.hidden = show ? 0 : 1),
		fields_dict: { timeline_links_sections: { head, is_collapsed: () => state.collapsed } },
	};
	return { frm, handlers, state };
}

test("folding Timeline Links with its chevron hides the whole section", () => {
	const { communication } = load();
	const { frm, handlers, state } = folding_frm();
	communication.bind_timeline_fold(frm, true);

	handlers["click.reyal-email"]({ type: "click" });
	assert.equal(state.hidden, 0);
	state.collapsed = true;
	handlers["keypress.reyal-email"]({ type: "keypress", key: "a" });
	assert.equal(state.hidden, 0);
	handlers["keypress.reyal-email"]({ type: "keypress", key: "Enter" });
	assert.equal(state.hidden, 1);
});

test("non-email records keep the stock chevron", () => {
	const { communication } = load();
	const { frm, handlers } = folding_frm();
	communication.bind_timeline_fold(frm, true);
	communication.bind_timeline_fold(frm, false);

	assert.equal(Object.keys(handlers).length, 0);
});

test("Contacts never appear under Linked to, addressed or not", () => {
	const { communication } = load();
	const html = communication.links_html(
		{
			reference_doctype: "Project",
			reference_name: "P1",
			timeline_links: [
				{ link_doctype: "Contact", link_name: "Team1" },
				{ link_doctype: "Contact", link_name: "Warehouse" },
				{ link_doctype: "Supplier", link_name: "S1" },
			],
		},
		false
	);

	assert.deepEqual(link_rows(html), ["Project P1", "Supplier S1"]);
});
