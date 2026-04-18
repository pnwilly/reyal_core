app_name = "reyal_core"
app_title = "Reyal Core"
app_publisher = "Patrick Willy"
app_description = "Quality-of-life enhancements for Frappe / ERPNext"
app_email = "pin@reyal.email"
app_license = "mit"

# Install / migrate hooks:

after_install = "reyal_core.setup.install.after_install"
after_migrate = "reyal_core.setup.install.after_install"

# Document events:

before_request = "reyal_core.overrides.apply_patches"

doc_events = {
	"User": {
		"on_update": "reyal_core.user.compute_short_name",
	}
}
