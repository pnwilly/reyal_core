import frappe
from frappe.model.document import Document


class ReyalSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		user_display_name_format: DF.Literal["Full Name", "First + Last Initial", "First Name Only"]

	# end: auto-generated types
