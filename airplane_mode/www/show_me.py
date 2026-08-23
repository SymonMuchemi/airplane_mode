import frappe


def get_context(context):
    context.color = frappe.form_dict.get("color") or "black"
