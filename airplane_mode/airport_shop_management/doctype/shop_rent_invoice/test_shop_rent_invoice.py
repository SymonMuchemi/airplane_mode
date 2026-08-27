# Copyright (c) 2026, SymonMuchemi and Contributors
# See license.txt

from uuid import uuid4

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, get_first_day, today


# On IntegrationTestCase, the doctype test records and all
# link-field test record dependencies are recursively loaded
# Use these module variables to add/remove to/from that list
EXTRA_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]
IGNORE_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]


class IntegrationTestShopRentInvoice(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		unique_id = uuid4().hex[:8]
		self.airport = frappe.get_doc(
			{
				"doctype": "Airport",
				"code": unique_id.upper(),
				"city": "Test City",
				"country": "Test Country",
			}
		).insert(set_name=f"Test Airport {unique_id}")
		self.shop_type = frappe.get_doc(
			{
				"doctype": "Shop Type",
				"type": f"Test Shop Type {unique_id}",
				"is_enabled": 1,
			}
		).insert()
		self.shop = frappe.get_doc(
			{
				"doctype": "Airport Shop",
				"airport": self.airport.name,
				"type": self.shop_type.name,
				"shop_number": f"SHOP-{unique_id}",
				"shop_name": f"Test Shop {unique_id}",
				"monthly_rent_amount": 1_500,
				"area": 25,
				"area_unit": "Square Meters",
			}
		).insert()
		self.tenant = frappe.get_doc(
			{
				"doctype": "Shop Tenant",
				"tenant_name": f"Test Tenant {unique_id}",
				"email": f"tenant-{unique_id}@example.com",
			}
		).insert()

	def test_invoice_uses_server_side_lease_values_and_prevents_duplicates(self):
		lease = self._make_lease()
		lease.submit()
		generated_invoice = frappe.get_doc(
			"Shop Rent Invoice",
			frappe.db.get_value("Shop Rent Invoice", {"lease": lease.name}, "name"),
		)
		generated_invoice.cancel()

		replacement_invoice = frappe.get_doc(
			{
				"doctype": "Shop Rent Invoice",
				"lease": lease.name,
				"billing_month": get_first_day(today()),
				"due_date": today(),
				"amount_due": 1,
			}
		).insert()

		self.assertEqual(replacement_invoice.airport, self.airport.name)
		self.assertEqual(replacement_invoice.shop, self.shop.name)
		self.assertEqual(replacement_invoice.tenant, self.tenant.name)
		self.assertEqual(replacement_invoice.amount_due, 1_500)
		self.assertEqual(replacement_invoice.outstanding_amount, 1_500)

		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				{
					"doctype": "Shop Rent Invoice",
					"lease": lease.name,
					"billing_month": get_first_day(today()),
					"due_date": today(),
					"amount_due": 1_500,
				}
			).insert()

	def test_invoice_requires_a_submitted_lease(self):
		draft_lease = self._make_lease()

		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				{
					"doctype": "Shop Rent Invoice",
					"lease": draft_lease.name,
					"billing_month": get_first_day(today()),
					"due_date": today(),
					"amount_due": 1_500,
				}
			).insert()

	def _make_lease(self):
		return frappe.get_doc(
			{
				"doctype": "Shop Lease",
				"shop": self.shop.name,
				"tenant": self.tenant.name,
				"start_date": today(),
				"end_date": add_days(today(), 20),
				"first_payment_due_date": today(),
				"monthly_rent_amount": 1_500,
			}
		).insert()
