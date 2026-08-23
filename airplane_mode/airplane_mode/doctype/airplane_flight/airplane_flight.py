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
