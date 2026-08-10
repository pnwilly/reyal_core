(function () {
	const PATCH_FLAG = "_reyal_notification_cleanup_patched_v5";
	const VIEW_PATCH_FLAG = "_reyal_notification_cleanup_view_patched_v5";
	const OBSERVER_FLAG = "_reyal_notification_delete_observer_v5";
	const DELETE_METHOD = "reyal_core.notifications.delete_notification";
	const DECORATED_ATTR = "data-reyal-decorated";

	function get_notifications_instance() {
		if (!frappe || !frappe.frappe_toolbar) return null;
		return frappe.frappe_toolbar.notifications;
	}

	function get_notifications_view(notifications) {
		if (!notifications || !notifications.tabs) return null;
		return notifications.tabs.notifications || null;
	}

	function remove_legacy_injected_styles() {
		[
			"#reyal-notification-cleanup-style",
			"#reyal-notification-row-delete-style-v2",
			"#reyal-notification-row-delete-style-v3",
		].forEach((selector) => $(selector).remove());
	}

	function remove_legacy_header_delete(notifications) {
		if (!notifications || !notifications.header_actions) return;
		notifications.header_actions
			.find('.clear-read-notifications, [data-action="clear_read_notifications"]')
			.remove();
	}

	/**
	 * Only real notification rows: anchor.notification-item with a Notification Log name.
	 * Never decorate tabs, footers, empty-states, or nested fragments.
	 */
	function get_rendered_notification_items(notifications) {
		const view = get_notifications_view(notifications);
		const $root = view && view.container && view.container.length
			? view.container
			: $(".dropdown-notifications .panel-notifications");

		return $root.find("a.notification-item[data-name]").filter(function () {
			// Exclude nested matches if Frappe ever wraps items.
			return $(this).closest("a.notification-item[data-name]").is(this);
		});
	}

	function make_delete_icon() {
		const svg_namespace = "http://www.w3.org/2000/svg";
		const svg = document.createElementNS(svg_namespace, "svg");
		svg.setAttribute("class", "icon icon-xs");
		svg.setAttribute("viewBox", "0 0 32 32");
		svg.setAttribute("fill", "none");
		svg.setAttribute("aria-hidden", "true");

		[
			"M7 7v18.118c0 2.145 1.492 3.882 3.333 3.882h11.333c1.842 0 3.333-1.737 3.333-3.882V7",
			"M5 7h22",
			"M10 7V6c0-1.657 1.343-3 3-3h6c1.657 0 3 1.343 3 3v1",
			"M18.8 14.4v8.571",
			"M13.2 14.4v8.571",
		].forEach((path_definition) => {
			const path = document.createElementNS(svg_namespace, "path");
			path.setAttribute("stroke", "currentColor");
			path.setAttribute("stroke-linejoin", "round");
			path.setAttribute("stroke-linecap", "round");
			path.setAttribute("stroke-miterlimit", "10");
			path.setAttribute("stroke-width", "2");
			path.setAttribute("d", path_definition);
			svg.appendChild(path);
		});

		return svg;
	}

	function sync_notification_icon(view) {
		if (!view || !view.toggle_notification_icon || !Array.isArray(view.dropdown_items)) return;

		const has_unread = view.dropdown_items.some((item) => !item.read);
		view.toggle_notification_icon(!has_unread);
	}

	function refresh_notifications_dropdown(notifications) {
		const view = get_notifications_view(notifications);
		if (!view || !view.get_notifications_list) return;

		view
			.get_notifications_list(view.max_length || 20)
			.then((r) => {
				if (!r || !r.message) {
					sync_notification_icon(view);
					return;
				}

				view.dropdown_items = r.message.notification_logs || [];
				frappe.update_user_info(r.message.user_info || {});
				view.container.empty();
				view.render_notifications_dropdown();

				sync_notification_icon(view);
			})
			.catch((error) => {
				console.error("Unable to refresh notifications dropdown", error);
				sync_notification_icon(view);
			});
	}

	function remove_notification_item_from_dom(docname) {
		if (!docname) return;
		$("a.notification-item[data-name]").filter(function () {
			return $(this).attr("data-name") === docname;
		}).remove();
	}

	function delete_notification_row(notifications, docname) {
		if (!docname) return;

		frappe.confirm(__("Delete this notification?"), () => {
			frappe.call({
				method: DELETE_METHOD,
				args: { docname },
				callback: (r) => {
					const deleted = (r && r.message && r.message.deleted) || 0;
					refresh_notifications_dropdown(notifications);
					if (!get_notifications_view(notifications)) {
						remove_notification_item_from_dom(docname);
					}
					if (deleted) {
						frappe.show_alert({
							message: __("Notification deleted"),
							indicator: "green",
						});
					}
				},
				error: () => {
					frappe.show_alert({
						message: __("Could not delete notification"),
						indicator: "red",
					});
				},
			});
		});
	}

	function make_delete_button(notifications, docname) {
		const label = __("Delete notification");
		const $delete = $(document.createElement("span"))
			.addClass("reyal-notification-delete")
			.attr({
				role: "button",
				tabindex: "0",
				"data-docname": docname,
				title: label,
				"aria-label": label,
			})
			.append(make_delete_icon());

		$delete.on("click", function (e) {
			e.preventDefault();
			e.stopImmediatePropagation();
			delete_notification_row(notifications, docname);
			return false;
		});

		$delete.on("keydown", function (e) {
			if (e.key === "Enter" || e.key === " ") {
				e.preventDefault();
				e.stopImmediatePropagation();
				delete_notification_row(notifications, docname);
			}
		});

		if ($.fn && $.fn.tooltip) {
			$delete.tooltip({ delay: { show: 600, hide: 100 }, trigger: "hover" });
		}
		return $delete;
	}

	function looks_like_email_html(html) {
		if (!html) return false;
		return /<(p|ul|ol|table|div|br|h[1-6])\b/i.test(html);
	}

	function plain_text_from_html(html) {
		if (typeof strip_html === "function") {
			return strip_html(html).replace(/\s+/g, " ").trim();
		}
		return $("<div/>").html(html).text().replace(/\s+/g, " ").trim();
	}

	/**
	 * Desk dropdowns should not render full email HTML bodies. When a
	 * Notification Log mirrored email_content into description (or stuffed
	 * HTML into the subject), collapse it to a short plain-text line.
	 */
	function sanitize_notification_item_body($item) {
		const $message = $item.children(".notification-body").children(".message").first();
		if (!$message.length) return;

		const $description = $message.children(".notification-description").first();
		if ($description.length && looks_like_email_html($description.html())) {
			const text = plain_text_from_html($description.html());
			if (text) {
				$description.text(frappe.ellipsis ? frappe.ellipsis(text, 140) : text.slice(0, 140));
			} else {
				$description.remove();
			}
		}

		$message.children("div").not(".notification-description, .notification-timestamp").each(function () {
			const $block = $(this);
			const html = $block.html() || "";
			if (!looks_like_email_html(html)) return;
			const text = plain_text_from_html(html);
			$block.text(frappe.ellipsis ? frappe.ellipsis(text, 140) : text.slice(0, 140));
		});
	}

	function decorate_notification_item($item, notifications) {
		const docname = $item.attr("data-name");
		if (!docname) return;

		// Already decorated for this log — avoid observer re-entry churn.
		if ($item.attr(DECORATED_ATTR) === docname && $item.children(".reyal-notification-controls").length) {
			return;
		}

		const is_unread = $item.hasClass("unread");
		$item.css({ position: "relative", "padding-right": "34px" });
		sanitize_notification_item_body($item);

		let $controls = $item.children(".reyal-notification-controls").first();
		if (!$controls.length) {
			$controls = $('<div class="reyal-notification-controls"></div>');
			$item.append($controls);
		}

		$item.find(".reyal-notification-delete").remove();
		$controls.prepend(make_delete_button(notifications, docname));

		let $mark = $item.children(".mark-as-read").first();
		if (!$mark.length) {
			$mark = $controls.children(".mark-as-read").first();
		}

		$item.find(".mark-as-read").not($mark).remove();
		if (is_unread && $mark.length) {
			if (!$mark.parent().is($controls)) {
				$controls.append($mark.detach());
			}
		} else if ($mark.length) {
			$mark.remove();
		}

		$item.find(".reyal-notification-actions").remove();
		$item.attr(DECORATED_ATTR, docname);
	}

	function decorate_notification_items(notifications) {
		remove_legacy_injected_styles();
		get_rendered_notification_items(notifications).each(function () {
			decorate_notification_item($(this), notifications);
		});
	}

	function observe_notification_panel(notifications) {
		const panel = $(".dropdown-notifications .panel-notifications").get(0);
		if (!panel || panel[OBSERVER_FLAG]) return;

		const observer_config = {
			attributes: true,
			attributeFilter: ["class"],
			childList: true,
			subtree: true,
		};

		// Decorating mutates the panel; disconnect first or we re-enter forever and
		// fragment rows (delete controls / layout applied over and over).
		const observer = new MutationObserver(() => {
			if (panel.__reyal_observer_busy_v5) return;
			panel.__reyal_observer_busy_v5 = true;
			try {
				observer.disconnect();
				// New/replaced rows need decoration; clear stamp when nodes are swapped.
				get_rendered_notification_items(notifications).each(function () {
					const $item = $(this);
					if (!$item.children(".reyal-notification-controls").length) {
						$item.removeAttr(DECORATED_ATTR);
					}
				});
				decorate_notification_items(notifications);
			} finally {
				panel.__reyal_observer_busy_v5 = false;
				observer.observe(panel, observer_config);
			}
		});

		observer.observe(panel, observer_config);
		panel[OBSERVER_FLAG] = observer;
	}

	function patch_notifications_view(notifications) {
		const view = get_notifications_view(notifications);
		if (!view || view[VIEW_PATCH_FLAG]) return;

		const original_render = view.render_notifications_dropdown;
		view.render_notifications_dropdown = function () {
			original_render.call(this);
			// Fresh render — allow redecorate.
			get_rendered_notification_items(notifications).removeAttr(DECORATED_ATTR);
			decorate_notification_items(notifications);
			remove_legacy_header_delete(notifications);
		};

		const original_insert = view.insert_into_dropdown;
		if (original_insert) {
			view.insert_into_dropdown = function () {
				original_insert.call(this);
				decorate_notification_items(notifications);
				remove_legacy_header_delete(notifications);
			};
		}

		view[VIEW_PATCH_FLAG] = true;
		decorate_notification_items(notifications);
		remove_legacy_header_delete(notifications);
	}

	function patch_notifications_class() {
		if (!frappe || !frappe.ui) return;
		const NotificationsClass = frappe.ui.Notifications;
		if (!NotificationsClass || NotificationsClass.prototype[PATCH_FLAG]) return;

		const original_make_tab_view = NotificationsClass.prototype.make_tab_view;
		NotificationsClass.prototype.make_tab_view = function (item) {
			original_make_tab_view.call(this, item);
			if (item && item.id === "notifications") {
				patch_notifications_view(this);
				remove_legacy_header_delete(this);
			}
		};

		NotificationsClass.prototype[PATCH_FLAG] = true;
	}

	function init() {
		if (!(frappe.boot && frappe.boot.desk_settings && frappe.boot.desk_settings.notifications)) return;

		patch_notifications_class();

		const notifications = get_notifications_instance();
		patch_notifications_view(notifications);
		decorate_notification_items(notifications);
		observe_notification_panel(notifications);
		remove_legacy_header_delete(notifications);
	}

	$(document).on("toolbar_setup", init);
	$(document).on("show.bs.dropdown shown.bs.dropdown", ".dropdown-notifications", init);
	$(init);
})();
