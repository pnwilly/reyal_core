(function () {
	const PATCH_FLAG = "_reyal_notification_cleanup_patched_v5";
	const VIEW_PATCH_FLAG = "_reyal_notification_cleanup_view_patched_v5";
	const DELETE_METHOD = "reyal_core.notifications.delete_notification";

	function get_notifications_instance() {
		if (!frappe || !frappe.frappe_toolbar) return null;
		return frappe.frappe_toolbar.notifications;
	}

	function remove_legacy_header_delete(notifications) {
		if (!notifications || !notifications.header_actions) return;
		notifications.header_actions
			.find('.clear-read-notifications, [data-action="clear_read_notifications"]')
			.remove();
	}

	function refresh_notifications_dropdown(notifications) {
		if (!notifications || !notifications.tabs) return;
		const view = notifications.tabs.notifications;
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

	function delete_notification_row(notifications, docname) {
		if (!docname) return;

		frappe.confirm(__("Delete this notification?"), () => {
			frappe.call({
				method: DELETE_METHOD,
				args: { docname },
				callback: (r) => {
					const deleted = (r && r.message && r.message.deleted) || 0;
					refresh_notifications_dropdown(notifications);
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

	function decorate_notification_items(notifications) {
		if (!notifications || !notifications.tabs) return;
		const view = notifications.tabs.notifications;
		if (!view || !view.container) return;

		view.container.find(".notification-item").each(function () {
			const $item = $(this);
			const docname = $item.attr("data-name");
			if (!docname) return;

			$item.css({ position: "relative", "padding-right": "48px" });

			$item.find(".reyal-notification-actions").each(function () {
				const $actions = $(this);
				const $mark = $actions.find(".mark-as-read").first();
				if ($mark.length) {
					$actions.before($mark);
				}
				$actions.remove();
			});

			$item.find(".reyal-notification-controls").each(function () {
				const $controls = $(this);
				const $mark = $controls.find(".mark-as-read").first();
				if ($mark.length) {
					$controls.before($mark);
				}
				$controls.remove();
			});

			$item.find(".reyal-notification-delete").remove();

			let $mark = null;
			$item.children(".mark-as-read").each(function (index) {
				if (index === 0) {
					$mark = $(this);
				} else {
					$(this).remove();
				}
			});

			const icon_html = frappe.utils.icon("delete");
			const $delete = $(
				`<span class="reyal-notification-delete" data-docname="${docname}" title="${__("Delete notification")}">${icon_html || "&times;"}</span>`
			);

			$delete.on("click", function (e) {
				e.preventDefault();
				e.stopImmediatePropagation();
				delete_notification_row(notifications, docname);
				return false;
			});
			$delete.tooltip({ delay: { show: 600, hide: 100 }, trigger: "hover" });

			const $controls = $('<div class="reyal-notification-controls"></div>');
			$controls.append($delete);
			if ($mark && $mark.length) {
				$controls.append($mark);
			}

			$item.append($controls);
		});
	}

	function patch_notifications_view(notifications) {
		if (!notifications || !notifications.tabs) return;
		const view = notifications.tabs.notifications;
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
		remove_legacy_header_delete(notifications);
	}

	$(document).on("toolbar_setup", init);
	$(init);
})();
