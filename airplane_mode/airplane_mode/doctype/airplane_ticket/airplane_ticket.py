# Copyright (c) 2025, SymonMuchemi and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class AirplaneTicket(Document):
    def before_save(self):
        """ensure the total amount payable by the passenger is calculated correctly."""
        add_ons_total = sum(add_on.amount for add_on in self.add_ons if add_on.amount)

        self.total_amount = self.flight_price + add_ons_total
