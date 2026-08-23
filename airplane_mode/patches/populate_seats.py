import frappe
import random

def execute():
	tickets = frappe.get_all("Airplane Ticket", fields=["name", "seat"])

	for ticket in tickets:
		if not ticket.seat:
			seat_number = generate_random_seat_number()
			frappe.db.set_value("Airplane Ticket", ticket.name, "seat", seat_number)

def generate_random_seat_number():
	row = random.randint(1, 100)  # 1-100
	column = random.choice(["A", "B", "C", "D", "E"])
	return f"{row}{column}"
