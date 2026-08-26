import frappe
from frappe import _

no_cache = 1


def get_context(context):
	shop_name = frappe.form_dict.get("shop")

	context.shop = frappe.db.get_value(
		"Airport Shop",
		shop_name,
		[
			"name",
			"shop_number",
			"shop_name",
			"airport",
			"status",
			"shop_image",
			"monthly_rent_amount",
			"area",
			"area_unit",
			"description",
		],
		as_dict=True,
	)

	if not context.shop:
		frappe.throw(_("Shop not found."), frappe.DoesNotExistError)
