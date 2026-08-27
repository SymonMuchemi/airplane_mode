# Copyright (c) 2026, SymonMuchemi and Contributors
# See license.txt

from uuid import uuid4

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, today


# On IntegrationTestCase, the doctype test records and all
# link-field test record dependencies are recursively loaded
# Use these module variables to add/remove to/from that list
EXTRA_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]
IGNORE_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]


class IntegrationTestShopRentPayment(IntegrationTestCase):
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
		self.lease = frappe.get_doc(
			{
				"doctype": "Shop Lease",
				"shop": self.shop.name,
				"tenant": self.tenant.name,
				"start_date": today(),
				"end_date": add_days(today(), 40),
				"first_payment_due_date": today(),
				"monthly_rent_amount": 1_500,
			}
		).insert()
		self.lease.submit()
		self.invoice = frappe.get_doc(
			"Shop Rent Invoice",
			frappe.db.get_value(
				"Shop Rent Invoice",
				{"lease": self.lease.name},
				"name",
				order_by="due_date asc",
			),
		)

	def test_partial_and_full_payments_recalculate_invoice(self):
		first_payment = self._make_payment(500)
		first_payment.submit()
		self.invoice.reload()

		self.assertEqual(self.invoice.paid_amount, 500)
		self.assertEqual(self.invoice.outstanding_amount, 1_000)
		self.assertEqual(self.invoice.status, "Partly Paid")
		self.assertEqual(first_payment.lease, self.lease.name)
		self.assertEqual(first_payment.airport, self.airport.name)
		self.assertEqual(first_payment.shop, self.shop.name)
		self.assertEqual(first_payment.tenant, self.tenant.name)

		second_payment = self._make_payment(
			1_000,
			payment_method="Bank Transfer",
			reference_number="BANK-001",
		)
		second_payment.submit()
		self.invoice.reload()

		self.assertEqual(self.invoice.paid_amount, 1_500)
		self.assertEqual(self.invoice.outstanding_amount, 0)
		self.assertEqual(self.invoice.status, "Paid")

		second_payment.cancel()
		self.invoice.reload()
		self.assertEqual(self.invoice.paid_amount, 500)
		self.assertEqual(self.invoice.outstanding_amount, 1_000)
		self.assertEqual(self.invoice.status, "Partly Paid")

	def test_overpayment_and_missing_reference_are_rejected(self):
		with self.assertRaises(frappe.ValidationError):
			self._make_payment(500, payment_method="Bank Transfer")

		overpayment = self._make_payment(1_501)
		with self.assertRaises(frappe.ValidationError):
			overpayment.submit()

	def test_submitted_payment_blocks_invoice_and_lease_cancellation(self):
		payment = self._make_payment(500)
		payment.submit()

		with self.assertRaises(frappe.ValidationError):
			self.invoice.cancel()

		with self.assertRaises(frappe.ValidationError):
			self.lease.cancel()

		payment.cancel()
		self.lease.reload()
		self.lease.cancel()

		self.assertFalse(
			frappe.db.exists(
				"Shop Rent Invoice",
				{"lease": self.lease.name, "docstatus": 1},
			)
		)

	def _make_payment(
		self,
		amount_paid,
		payment_method="Cash",
		reference_number=None,
	):
		return frappe.get_doc(
			{
				"doctype": "Shop Rent Payment",
				"rent_invoice": self.invoice.name,
				"payment_date": today(),
				"amount_paid": amount_paid,
				"payment_method": payment_method,
				"reference_number": reference_number,
			}
		).insert()
