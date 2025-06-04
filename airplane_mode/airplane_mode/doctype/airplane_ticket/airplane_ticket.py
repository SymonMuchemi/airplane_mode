# Copyright (c) 2025, SymonMuchemi and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from random import randint, choice


class AirplaneTicket(Document):
    def before_save(self):
        self.calculate_total_amount()

    def before_insert(self):
        """Set the ticket seat to a string before inserting."""
        self.seat = f"{randint(1, 100)}{choice(['A', 'B', 'C', 'D', 'E'])}"

    def before_submit(self):
        """Ensure the ticket is validated before submission."""
        self.ensure_boarded_status()

    def calculate_total_amount(self):
        """ensure the total amount payable by the passenger is calculated correctly."""
        add_ons_total = sum(add_on.amount for add_on in self.add_ons if add_on.amount)

        self.total_amount = self.flight_price + add_ons_total

    def validate(self):
        """Validate the ticket before saving."""
        self.check_duplicate_add_ons()

    def check_duplicate_add_ons(self):
        """Check for duplicate add-ons in the ticket."""
        add_on_set = set()

        if self.add_ons:
            add_on_set = set([add_on.item for add_on in self.add_ons])

        if len(add_on_set) != len(self.add_ons):
            frappe.throw(
                "Duplicate add-ons are not allowed. Please check your add-ons list."
            )

        print("Add-ons validated successfully.")

    def ensure_boarded_status(self):
        """Ensure that the ticket is marked as boarded."""
        if self.status != "Boarded":
            frappe.throw(
                "Ticket must be marked as 'Boarded' before proceeding. Please update the status."
            )
