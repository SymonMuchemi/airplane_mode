# Copyright (c) 2025, SymonMuchemi and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class AirplaneFlight(Document):
    def on_submit(self):
        """Set the status of to 'Completed' when the flight is submitted."""
        self.status = "Completed"
