import frappe
import random
import string

def execute():
	tickets = frappe.get_all("Airplane Ticket", fields=["name", "seat"])

	for ticket in tickets:
		if not ticket.seat:
			seat_number = generate_random_seat_number()
			frappe.db.set_value("Airplane Ticket", ticket.name, "seat", seat_number)

def generate_random_seat_number():
	row = random.randint(1, 30)  # 1-30
	column = random.choice(string.ascii_uppercase[:26])  # A-Z
	return f"{row}{column}"
