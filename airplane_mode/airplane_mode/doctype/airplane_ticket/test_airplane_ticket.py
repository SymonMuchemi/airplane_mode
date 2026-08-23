# Copyright (c) 2026, SymonMuchemi and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase


# On IntegrationTestCase, the doctype test records and all
# link-field test record dependencies are recursively loaded
# Use these module variables to add/remove to/from that list
EXTRA_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]
IGNORE_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]


class IntegrationTestAirplaneTicket(IntegrationTestCase):
	"""
	Integration tests for AirplaneTicket.
	Use this class for testing interactions between multiple components.
	"""

	def test_before_save_accepts_string_flight_price_without_add_ons(self):
		ticket = frappe.new_doc("Airplane Ticket")
		ticket.flight_price = "1000.00"

		ticket.before_save()

		self.assertEqual(ticket.total_amount, 1000.0)

	def test_before_save_accepts_currency_strings(self):
		ticket = frappe.new_doc("Airplane Ticket")
		ticket.flight_price = "1000.25"
		ticket.append("add_ons", {"amount": "125.50"})
		ticket.append("add_ons", {"amount": "74.25"})

		ticket.before_save()

		self.assertEqual(ticket.total_amount, 1200.0)
