# Copyright (c) 2026, SymonMuchemi and contributors
# For license information, please see license.txt

import random
import frappe
from frappe.model.document import Document
from frappe.utils import flt


class AirplaneTicket(Document):
	def validate(self):
		add_on_types = [item.item for item in self.add_ons]
		if len(add_on_types) != len(set(add_on_types)):
			frappe.throw("You cannot add more than one add-on of the same type.")

	def before_save(self):
		if not self.flight_price:
			self.flight_price = 1000  # Default flight price if not provided
		total_add_ons_amount = sum(flt(item.amount) for item in self.add_ons)
		self.total_amount = flt(self.flight_price) + total_add_ons_amount
		self.seat = self.generate_random_seat_number()

	def before_submit(self):
		if self.status != "Boarded":
			frappe.throw("You can only submit the ticket if the status is 'Boarded'.")

	def generate_random_seat_number(self):
		# Generate a random seat number in the format "A1", "B2", etc.
		row = random.randint(1, 100)  # 1-100
		column = random.choice(["A", "B", "C", "D", "E"])  # A-Z
		return f"{row}{column}"
