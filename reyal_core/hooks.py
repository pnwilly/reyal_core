app_name = "reyal_core"
app_title = "Reyal"
app_publisher = "Reyal"
app_description = "Shared Reyal utilities for Frappe: short display names and Desk notification actions"
app_email = "oss@reyal.email"
app_license = "mit"

# Include custom Desk behaviour:
app_include_js = [
	"/assets/reyal_core/js/notification_row_delete_v5.js?v=20261111_02",
	"/assets/reyal_core/js/view_amendment.js?v=20261112_02",
]
app_include_css = "/assets/reyal_core/css/notification_row_delete_v5.css?v=20261111_02"

# Install / migrate hooks:

after_install = "reyal_core.setup.install.after_install"
after_migrate = "reyal_core.setup.install.after_install"

# Document events:

before_request = [
	"reyal_core.overrides.apply_patches",
	"reyal_core.amendments.patch_amended_deletion",
]
before_job = ["reyal_core.amendments.patch_amended_deletion"]

doc_events = {
	"*": {
		"on_trash": "reyal_core.amendments.keep_series_of_amended_original",
	},
	"User": {
		"on_update": "reyal_core.user.compute_short_name",
	},
}
