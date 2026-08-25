# Copyright (c) 2026, SymonMuchemi and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class AirportShop(Document):
    def validate(self):
        default_rent_amount = frappe.get_single_value(
            "Airport Shop Settings", "default_rent_amount"
        )
        if (self.monthly_rent_amount == 0) and (default_rent_amount > 0.00):
            self.monthly_rent_amount = default_rent_amount
