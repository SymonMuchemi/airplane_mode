# Copyright (c) 2026, SymonMuchemi and contributors
# For license information, please see license.txt

import frappe

from frappe.website.website_generator import WebsiteGenerator


class AirplaneFlight(WebsiteGenerator):
    def validate(self):
        if not self.route:
            self.route = "flights/" + frappe.scrub(self.name)

    def before_submit(self):
        self.status = "Completed"

    def on_update_after_submit(self):
        self._enqueue_gate_sync()

    def on_update(self):
        self._enqueue_gate_sync()

    def _enqueue_gate_sync(self):
        old_doc = self.get_doc_before_save()

        if not old_doc or not self.has_value_changed("gate"):
            return

        frappe.enqueue(
            sync_gate_to_tickets,
            queue="short",
            enqueue_after_commit=True,
            flight_name=self.name,
        )


def sync_gate_to_tickets(flight_name):
    current_gate = frappe.db.get_value("Airplane Flight", flight_name, "gate")

    frappe.db.set_value(
        "Airplane Ticket", {"flight": flight_name}, "gate", current_gate
    )
