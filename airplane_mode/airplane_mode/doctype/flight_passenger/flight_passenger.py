# Copyright (c) 2025, SymonMuchemi and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class FlightPassenger(Document):
    @property
    def full_name(self):
        """Returns the full name of the passenger."""
        return f"{self.first_name} {self.last_name}"
