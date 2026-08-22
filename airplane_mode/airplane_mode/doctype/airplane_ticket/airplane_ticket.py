# Copyright (c) 2026, SymonMuchemi and contributors
# For license information, please see license.txt

import frappe
import random
import string
from frappe.model.document import Document


class AirplaneTicket(Document):
	def validate(self):
		add_on_types = [item.item for item in self.add_ons]
		if len(add_on_types) != len(set(add_on_types)):
			frappe.throw("You cannot add more than one add-on of the same type.")


	def before_save(self):
		total_add_ons_amount = 0

		for item in self.add_ons:
			total_add_ons_amount += item.amount

		self.total_amount = self.flight_price + total_add_ons_amount
		self.seat = self.generate_random_seat_number()


	def before_submit(self):
		if self.status != "Boarded":
			frappe.throw("You can only submit the ticket if the status is 'Boarded'.")

	def generate_random_seat_number(self):
		# Generate a random seat number in the format "A1", "B2", etc.
		row = random.randint(1, 30)  # 1-30
		column = random.choice(string.ascii_uppercase[:26])  # A-Z
		return f"{row}{column}"
