app_name = "reyal_core"
app_title = "Reyal"
app_publisher = "Reyal"
app_description = "Shared Frappe utilities used by Reyal sites and apps"
app_email = "oss@reyal.email"
app_license = "mit"

# Include custom Desk behaviour:
app_include_js = [
	"/assets/reyal_core/js/notification_row_delete_v5.js?v=20261111_02",
	"/assets/reyal_core/js/view_amendment.js?v=20261112_02",
]
app_include_css = [
	"/assets/reyal_core/css/notification_row_delete_v5.css?v=20261111_02",
	"/assets/reyal_core/css/communication_form.css?v=20261119_22",
]
doctype_js = {"Communication": "public/js/communication_form.js"}

naming_series_variables = {
	"ENDYY": "reyal_core.payroll.payroll_end_year",
	"ENDMM": "reyal_core.payroll.payroll_end_month",
	"FROMYY": "reyal_core.payroll.from_year",
	"FROMMM": "reyal_core.payroll.from_month",
	"PAYYY": "reyal_core.payroll.payroll_year",
	"PAYMM": "reyal_core.payroll.payroll_month",
	"POSTYY": "reyal_core.naming.posting_year",
	"POSTMM": "reyal_core.naming.posting_month",
	"DATEYY": "reyal_core.naming.date_year",
	"DATEMM": "reyal_core.naming.date_month",
	"TRANSYY": "reyal_core.naming.transaction_year",
	"TRANSMM": "reyal_core.naming.transaction_month",
	"ABBR": "reyal_core.naming.company_abbr",
}

extend_doctype_class = {"Share Transfer": ["reyal_core.shares.ShareTransferFolio"]}

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
	"Communication": {
		"onload": "reyal_core.communication.add_names",
	},
	# Drafts named by a date are renamed when the date moves them to another period.
	"Payment Entry": {
		"before_insert": "reyal_core.drafts.set_draft_series",
		"before_validate": "reyal_core.drafts.keep_draft_name_current",
	},
	"Journal Entry": {"before_validate": "reyal_core.drafts.keep_draft_name_current"},
	"Purchase Invoice": {"before_validate": "reyal_core.drafts.keep_draft_name_current"},
	"Purchase Receipt": {"before_validate": "reyal_core.drafts.keep_draft_name_current"},
	"Sales Order": {"before_validate": "reyal_core.drafts.keep_draft_name_current"},
	"Share Transfer": {"before_validate": "reyal_core.drafts.keep_draft_name_current"},
	"Payroll Entry": {"before_validate": "reyal_core.drafts.keep_draft_name_current"},
	"Salary Structure Assignment": {"before_validate": "reyal_core.drafts.keep_draft_name_current"},
	"Additional Salary": {"before_validate": "reyal_core.drafts.keep_draft_name_current"},
	"Holiday List Assignment": {"before_validate": "reyal_core.drafts.keep_draft_name_current"},
}
