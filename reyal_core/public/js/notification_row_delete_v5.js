(function () {
	const PATCH_FLAG = "_reyal_notification_cleanup_patched_v5";
	const VIEW_PATCH_FLAG = "_reyal_notification_cleanup_view_patched_v5";
	const OBSERVER_FLAG = "_reyal_notification_delete_observer_v5";
	const DELETE_METHOD = "reyal_core.notifications.delete_notification";

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

	function get_rendered_notification_items(notifications) {
		const $items = $(".dropdown-notifications .panel-notifications .notification-item");
		if ($items.length) return $items;

		const view = get_notifications_view(notifications);
		return view && view.container ? view.container.find(".notification-item") : $();
	}

	function get_delete_icon() {
		const icon_html = frappe.utils.icon("delete", "xs", "", "--icon-stroke: currentColor;");
		if (icon_html) return icon_html;

		return `<svg class="icon icon-xs" viewBox="0 0 32 32" fill="none" aria-hidden="true">
			<path stroke="currentColor" stroke-linejoin="round" stroke-linecap="round" stroke-miterlimit="10" stroke-width="2" d="M7 7v18.118c0 2.145 1.492 3.882 3.333 3.882h11.333c1.842 0 3.333-1.737 3.333-3.882V7"></path>
			<path stroke="currentColor" stroke-linejoin="round" stroke-linecap="round" stroke-miterlimit="10" stroke-width="2" d="M5 7h22"></path>
			<path stroke="currentColor" stroke-linejoin="round" stroke-linecap="round" stroke-miterlimit="10" stroke-width="2" d="M10 7V6c0-1.657 1.343-3 3-3h6c1.657 0 3 1.343 3 3v1"></path>
			<path stroke="currentColor" stroke-linejoin="round" stroke-linecap="round" stroke-miterlimit="10" stroke-width="2" d="M18.8 14.4v8.571"></path>
			<path stroke="currentColor" stroke-linejoin="round" stroke-linecap="round" stroke-miterlimit="10" stroke-width="2" d="M13.2 14.4v8.571"></path>
		</svg>`;
	}

	function refresh_notifications_dropdown(notifications) {
		const view = get_notifications_view(notifications);
		if (!view || !view.get_notifications_list) return;

		view.get_notifications_list(view.max_length || 20).then((r) => {
			if (!r || !r.message) return;

			view.dropdown_items = r.message.notification_logs || [];
			frappe.update_user_info(r.message.user_info || {});
			view.container.empty();
			view.render_notifications_dropdown();

			const has_unread = view.dropdown_items.some((item) => !item.read);
			view.toggle_notification_icon(!has_unread);
		});
	}

	function remove_notification_item_from_dom(docname) {
		if (!docname) return;
		$(".dropdown-notifications .panel-notifications .notification-item").filter(function () {
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
		const $delete = $(
			`<span class="reyal-notification-delete" role="button" tabindex="0" data-docname="${docname}" title="${__("Delete notification")}" aria-label="${__("Delete notification")}">${get_delete_icon()}</span>`
		);

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

		$delete.tooltip({ delay: { show: 600, hide: 100 }, trigger: "hover" });
		return $delete;
	}

	function decorate_notification_item($item, notifications) {
		const docname = $item.attr("data-name");
		if (!docname) return;

		const is_unread = $item.hasClass("unread");
		$item.removeClass("reyal-row-actions-visible");
		$item.css({ position: "relative", "padding-right": "34px" });

		let $controls = $item.children(".reyal-notification-controls").first();
		if (!$controls.length) {
			$controls = $('<div class="reyal-notification-controls"></div>');
			$item.append($controls);
		}

		const $existing_delete = $controls.children(".reyal-notification-delete").first();
		if ($existing_delete.length) {
			$item.find(".reyal-notification-delete").not($existing_delete).remove();
		} else {
			$item.find(".reyal-notification-delete").remove();
			$controls.prepend(make_delete_button(notifications, docname));
		}

		let $mark = $controls.children(".mark-as-read").first();
		if (!$mark.length) {
			$mark = $item.children(".mark-as-read").first();
		}
		if (!$mark.length) {
			$mark = $item.find(".mark-as-read").first();
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

		const observer = new MutationObserver(() => decorate_notification_items(notifications));
		observer.observe(panel, {
			attributes: true,
			attributeFilter: ["class"],
			childList: true,
			subtree: true,
		});
		panel[OBSERVER_FLAG] = observer;
	}

	function patch_notifications_view(notifications) {
		const view = get_notifications_view(notifications);
		if (!view || view[VIEW_PATCH_FLAG]) return;

		const original_render = view.render_notifications_dropdown;
		view.render_notifications_dropdown = function () {
			original_render.call(this);
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
