import frappe

no_cache = 1


def get_context(context):
    context.shops = frappe.get_all(
        "Airport Shop",
        fields=[
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
        order_by="airport asc, shop_number asc",
    )
