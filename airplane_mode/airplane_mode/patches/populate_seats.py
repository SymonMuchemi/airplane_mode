import frappe
from random import randint, choice


def execute():
    # get all existing Airplane Tickets
    tickets = frappe.get_all("Airplane Ticket", fields=["name"])

    for name in tickets:
        ticket = frappe.get_doc("Airplane Ticket", name.name)

        if ticket.seat:
            # skip if seat is already assigned
            continue

        # assign random seat numbers
        ticket.seat = f"{randint(1, 99)}{choice(['A', 'B', 'C', 'D', 'E'])}"

        # save the ticket
        ticket.save(ignore_permissions=True)

    frappe.db.commit()
