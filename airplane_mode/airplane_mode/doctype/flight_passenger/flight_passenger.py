# Copyright (c) 2025, SymonMuchemi and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class FlightPassenger(Document):
    @property
    def full_name(self):
        """Returns the full name of the passenger."""
        return f"{self.first_name} {self.last_name}"

    @property
    def total_amount(self):
        """Returns the total amount payable by the passenger."""
        add_ons_total = sum(add_on.amount for add_on in self.add_ons if add_on.amount)

        return self.flight_price + add_ons_total
