frappe.provide("reyal_core.communication");

reyal_core.communication.STOCK_SECTIONS = [
	"subject",
	"section_break_10",
	"status_section",
	"additional_info",
	"reference_section",
	"email_inbox",
	"timeline_links_sections",
];

reyal_core.communication.FAILED_DELIVERY = [
	"Bounced",
	"Soft-Bounced",
	"Rejected",
	"Error",
	"Expired",
	"Marked As Spam",
];

reyal_core.communication.DIRECTION_ICONS = {
	Sent: "arrow-up-right",
	Received: "arrow-down-left",
};

/** Show a saved email Communication as a message: pinned subject, header card, then the body. */
reyal_core.communication.is_email_view = (frm) =>
	!frm.is_new() && frm.doc.communication_medium === "Email";

/** User date and time to the minute, in the user's time zone. */
reyal_core.communication.datetime_to_user = (value) => {
	const date_format = frappe.datetime.get_user_date_fmt().toUpperCase();
	const time_format = frappe.datetime.get_user_time_fmt().replace(":ss", "");
	return frappe.datetime.convert_to_user_tz(value, false).format(`${date_format} ${time_format}`);
};

/** Short age with "ago" ("8 h ago"); Frappe's own timestamps drop it. */
reyal_core.communication.age_text = (value) => {
	const age = frappe.datetime.prettyDate(value, true);
	return !age || age === __("now") ? age : __("{0} ago", [age]);
};

reyal_core.communication.age_html = (value) =>
	`<span class="reyal-email-ago" data-timestamp="${frappe.utils.escape_html(value)}"
		title="${reyal_core.communication.datetime_to_user(value)}">${reyal_core.communication.age_text(value)}</span>`;

reyal_core.communication.refresh_ages = () =>
	$(".reyal-email-ago[data-timestamp]").each((index, element) => {
		element.textContent = reyal_core.communication.age_text(element.dataset.timestamp);
	});

reyal_core.communication.email_of = (address) =>
	(address.match(/<([^>]+)>/)?.[1] || address).trim().toLowerCase();

/** The saved name of the Contact an address belongs to, from the email's timeline links. */
reyal_core.communication.contact_of = (doc, address, contacts) => {
	const name = contacts[reyal_core.communication.email_of(address)];
	if (!name) return null;
	const row = (doc.timeline_links || []).find(
		(link) => link.link_doctype === "Contact" && link.link_name === name
	);
	return { name, title: row?.link_title || name };
};

/** A Contact's saved name linking to it, with the address on hover; other addresses as written. */
reyal_core.communication.person_html = (doc, address, contacts) => {
	const escape = frappe.utils.escape_html;
	const contact = reyal_core.communication.contact_of(doc, address, contacts);
	if (!contact) return escape(address);
	const href = escape(frappe.utils.get_form_link("Contact", contact.name));
	return `<a class="reyal-email-link" href="${href}" title="${escape(address)}">${escape(contact.title)}</a>`;
};

reyal_core.communication.addresses_html = (doc, text, contacts = {}) =>
	frappe.utils
		.split_emails(text)
		.map((address) => reyal_core.communication.person_html(doc, address, contacts))
		.join(", ");

reyal_core.communication.sender_html = (doc, contacts = {}) => {
	const escape = frappe.utils.escape_html;
	const contact = doc.sender && reyal_core.communication.contact_of(doc, doc.sender, contacts);
	const name = contact?.title || doc.sender_full_name || doc.sender || __("Unknown sender");
	const address = doc.sender && doc.sender !== name ? doc.sender : "";
	const avatar = doc.user
		? frappe.avatar(doc.user, "avatar-medium")
		: frappe.get_avatar("avatar-medium", name);
	const name_html = contact ? reyal_core.communication.person_html(doc, doc.sender, contacts) : escape(name);
	return { avatar, name: name_html, address: escape(address) };
};

reyal_core.communication.link_html = (doctype, name, title) => {
	const escape = frappe.utils.escape_html;
	const href = escape(frappe.utils.get_form_link(doctype, name));
	return `<a class="reyal-email-link" href="${href}">${escape(title || name)}</a>`;
};

/** Documents grouped by type in first-seen order, as [type, [link html, …]] pairs. */
reyal_core.communication.link_groups = (links, short_names = {}) => {
	const groups = new Map();
	for (const { link_doctype, link_name, link_title } of links) {
		const user_name = link_doctype === "User" && short_names[String(link_name).toLowerCase()];
		if (!groups.has(link_doctype)) groups.set(link_doctype, []);
		groups.get(link_doctype).push(
			reyal_core.communication.link_html(link_doctype, link_name, user_name || link_title)
		);
	}
	return [...groups];
};

/** One row per type: the type once, then its documents in their own column so a long list wraps past the type. */
reyal_core.communication.link_row_html = (doctype, items_html) =>
	`<div class="reyal-email-link-group"><span class="reyal-email-doctype">${frappe.utils.escape_html(__(doctype))}</span> <span class="reyal-email-link-items">${items_html}</span></div>`;

reyal_core.communication.chip_html = (label, color) =>
	`<span class="indicator-pill ${color} reyal-email-chip">${frappe.utils.escape_html(label)}</span>`;

/** Only facts the title, toolbar and sidebar do not already show. */
reyal_core.communication.chips_html = (doc) => {
	const { chip_html, FAILED_DELIVERY } = reyal_core.communication;
	const chips = [];
	if (FAILED_DELIVERY.includes(doc.delivery_status)) chips.push(chip_html(__(doc.delivery_status), "red"));
	if (doc.read_by_recipient) {
		const on = doc.read_by_recipient_on ? ` ${reyal_core.communication.datetime_to_user(doc.read_by_recipient_on)}` : "";
		chips.push(chip_html(`${__("Read")}${on}`, "green"));
	}
	return chips.length ? `<div class="reyal-email-chips">${chips.join("")}</div>` : "";
};

/** A labelled header line; long values wrap under the value, not the label. */
reyal_core.communication.line_html = (label, body) =>
	`<div class="reyal-email-line"><span class="reyal-email-label">${label}</span><span class="reyal-email-value">${body}</span></div>`;

/** Timeline links other than the reference; Contacts belong to the From, To, Cc and Bcc lines, not here. */
reyal_core.communication.other_links = (doc) =>
	(doc.timeline_links || []).filter(
		(row) =>
			row.link_doctype !== "Contact" &&
			!(row.link_doctype === doc.reference_doctype && row.link_name === doc.reference_name)
	);

/** One Linked to line: the reference first, then the other documents, each document type on its own row. */
reyal_core.communication.links_html = (
	doc,
	can_edit,
	{ short_names = {}, reference_title = null } = {}
) => {
	const { link_groups, link_row_html, other_links, line_html } = reyal_core.communication;
	const reference = doc.reference_doctype && doc.reference_name
		? [{ link_doctype: doc.reference_doctype, link_name: doc.reference_name, link_title: reference_title }]
		: [];
	const groups = link_groups([...reference, ...other_links(doc)], short_names);
	if (!groups.length && !can_edit) return "";
	const edit = can_edit ? ` <a class="reyal-email-edit-links">${__("Edit")}</a>` : "";
	const rows = groups.map(([doctype, items], index) =>
		link_row_html(doctype, items.join(", ") + (index === groups.length - 1 ? edit : ""))
	);
	const body = rows.join("") || `<span class="text-muted">${__("None")}</span>${edit}`;
	return line_html(__("Linked to"), body);
};

reyal_core.communication.header_html = (
	doc,
	{ can_edit = false, short_names = {}, contacts = {}, reference_title = null } = {}
) => {
	const { addresses_html, sender_html, chips_html, links_html } = reyal_core.communication;
	const sender = sender_html(doc, contacts);
	const line = (label, text) =>
		text
			? reyal_core.communication.line_html(label, addresses_html(doc, text, contacts))
			: "";
	const date = reyal_core.communication.date_html(doc);
	return `<div class="reyal-email-header">
		<div class="reyal-email-meta">
			${sender.avatar}
			<div class="reyal-email-people">
				<div class="reyal-email-from">
					<span class="reyal-email-name">${sender.name}</span>
					${sender.address ? `<span class="reyal-email-address">&lt;${sender.address}&gt;</span>` : ""}
				</div>
				${line(__("To"), doc.recipients)}
				${line(__("Cc"), doc.cc)}
				${line(__("Bcc"), doc.bcc)}
			</div>
			${date}
		</div>
		${chips_html(doc)}
		<div class="reyal-email-links">${links_html(doc, can_edit, { short_names, reference_title })}</div>
	</div>`;
};

reyal_core.communication.date_html = (doc) =>
	doc.communication_date
		? `<div class="reyal-email-date">${reyal_core.communication.datetime_to_user(doc.communication_date)}
			${reyal_core.communication.age_html(doc.communication_date)}</div>`
		: "";

/** In the sidebar meta details, show the ID in the title row, then the date below the whole row, right-aligned. */
reyal_core.communication.set_sidebar_details = (frm, email_view) => {
	const meta = $(frm.page.sidebar).find(".sidebar-meta-details");
	const title_row = meta.find(".form-title-text");
	const was_email_view = meta.hasClass("reyal-email-meta");
	meta.removeClass("reyal-email-meta").find(".reyal-email-sidebar-date").remove();
	if (email_view || was_email_view) {
		const text = email_view ? frm.doc.name : frm.get_title();
		title_row.attr("data-copy", text).find("span").first().text(text);
	}
	const date = email_view && title_row.length ? reyal_core.communication.date_html(frm.doc) : "";
	if (date) meta.children(".flex").first().after(`<div class="reyal-email-sidebar-date">${date}</div>`);
	meta.toggleClass("reyal-email-meta", Boolean(email_view && title_row.length));
	$(frm.wrapper).toggleClass("reyal-email-date-in-sidebar", Boolean(date));
};

/** The subject sits outside the header card so it can stay pinned under the top bar for the whole email. */
reyal_core.communication.subject_html = (doc) =>
	`<div class="reyal-email-subject">${frappe.utils.escape_html(doc.subject || __("(No subject)"))}</div>`;

/** Rarely needed fields, collapsed below the message. */
reyal_core.communication.details_html = (doc) => {
	const { link_html } = reyal_core.communication;
	const escape = frappe.utils.escape_html;
	const rows = [
		[__("Email Account"), doc.email_account && link_html("Email Account", doc.email_account)],
		[__("In Reply To"), doc.in_reply_to && link_html("Communication", doc.in_reply_to)],
		[__("Email Template"), doc.email_template && link_html("Email Template", doc.email_template)],
		[__("Send After"), doc.send_after && reyal_core.communication.datetime_to_user(doc.send_after)],
		[__("Message ID"), doc.message_id && `<code>${escape(doc.message_id)}</code>`],
	].filter(([, value]) => value);
	if (!rows.length) return "";
	const items = rows.map(([label, value]) => `<dt>${label}</dt><dd>${value}</dd>`).join("");
	return `<details class="reyal-email-details">
		<summary>${__("Details")}</summary>
		<dl>${items}</dl>
	</details>`;
};

/** Name the list crumb after the medium (Email, Phone…) and open the list filtered by it. */
reyal_core.communication.set_medium_crumb = (page, medium) => {
	const items = page.get_breadcrumbs().slice();
	if (!medium || medium === "Other" || items.length < 2 || !items[0].href) return;
	const filter = `communication_medium=${encodeURIComponent(medium)}`;
	items[0] = { ...items[0], label: __(medium), href: `${items[0].href}?${filter}` };
	page.set_breadcrumbs(items);
};

/** Shrink the title crumb to a direction arrow; the email card shows the full subject. */
reyal_core.communication.set_direction = (page, direction) => {
	const icon = reyal_core.communication.DIRECTION_ICONS[direction];
	const items = page.get_breadcrumbs().slice();
	if (!icon || !items.length) return;
	const title = `${__(direction)}: ${page.title}`;
	page.set_breadcrumbs([...items.slice(0, -1), { title, prefix: icon }]);
};

/** Edit opens the stock Timeline Links section; a second click hides it again. */
reyal_core.communication.toggle_timeline_links = (frm) => {
	const is_open = !frm.get_docfield("timeline_links_sections").hidden;
	frm.toggle_display("timeline_links_sections", !is_open);
	if (is_open) return;
	const section = frm.fields_dict.timeline_links_sections;
	section.collapse(false);
	frappe.utils.scroll_to(section.wrapper);
};

/** Folding Timeline Links with its chevron hides the whole section, the same as a second click on Edit. */
reyal_core.communication.bind_timeline_fold = (frm, email_view) => {
	const section = frm.fields_dict.timeline_links_sections;
	if (!section?.head) return;
	section.head.off(".reyal-email");
	if (!email_view) return;
	section.head.on("click.reyal-email keypress.reyal-email", (event) => {
		if (event.type === "keypress" && event.key !== "Enter") return;
		if (section.is_collapsed()) frm.toggle_display("timeline_links_sections", false);
	});
};

reyal_core.communication.render = (frm) => {
	const { header_html, details_html, toggle_timeline_links } = reyal_core.communication;
	const header = $(
		header_html(frm.doc, {
			can_edit: frm.has_perm("write"),
			short_names: frm.doc.__onload?.short_names || {},
			contacts: frm.doc.__onload?.contacts || {},
			reference_title: frm.doc.__onload?.reference_title,
		})
	);
	header.find(".reyal-email-edit-links").on("click", () => toggle_timeline_links(frm));
	frm.layout.wrapper.prepend(header).prepend(reyal_core.communication.subject_html(frm.doc));
	if (frm.doc.reference_name) frm.remove_custom_button(__(frm.doc.reference_name));
	frm.fields_dict.content.$wrapper.closest(".form-section").after(details_html(frm.doc));
};

setInterval(reyal_core.communication.refresh_ages, 60000);

frappe.ui.form.on("Communication", {
	refresh(frm) {
		const {
			is_email_view,
			render,
			set_medium_crumb,
			set_direction,
			set_sidebar_details,
			bind_timeline_fold,
			STOCK_SECTIONS,
		} = reyal_core.communication;
		const email_view = is_email_view(frm);
		const direction = email_view ? frm.doc.sent_or_received : null;
		$(frm.wrapper).toggleClass("reyal-email-view", email_view);
		$(frm.page.wrapper)
			.toggleClass("reyal-email-sent", direction === "Sent")
			.toggleClass("reyal-email-received", direction === "Received");
		if (!frm.is_new()) set_medium_crumb(frm.page, frm.doc.communication_medium);
		set_direction(frm.page, direction);
		frm.toggle_display(STOCK_SECTIONS, !email_view);
		frm.layout.wrapper.find(".reyal-email-subject, .reyal-email-header, .reyal-email-details").remove();
		if (email_view) render(frm);
		set_sidebar_details(frm, email_view);
		bind_timeline_fold(frm, email_view);
	},
});
