# Copyright (c) 2026, SymonMuchemi and Contributors
# See license.txt

from uuid import uuid4

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, today

from airplane_mode.airport_shop_management.doctype.shop_lease.shop_lease import (
	generate_rent_invoices,
)


# On IntegrationTestCase, the doctype test records and all
# link-field test record dependencies are recursively loaded
# Use these module variables to add/remove to/from that list
EXTRA_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]
IGNORE_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]


class IntegrationTestShopLease(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		unique_id = uuid4().hex[:8]
		self.airport = self._make_airport(unique_id)
		self.shop = frappe.get_doc(
			{
				"doctype": "Airport Shop",
				"airport": self.airport.name,
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

	def test_submit_and_cancel_update_lease_and_shop_statuses(self):
		lease = self._make_lease(
			start_date=add_days(today(), -1),
			end_date=add_days(today(), 30),
			first_payment_due_date=today(),
		)

		lease.submit()

		self.assertEqual(lease.status, "Active")
		self.assertEqual(
			frappe.db.get_value("Airport Shop", self.shop.name, "status"), "Occupied"
		)

		lease.cancel()

		self.assertEqual(lease.status, "Cancelled")
		self.assertEqual(
			frappe.db.get_value("Airport Shop", self.shop.name, "status"), "Available"
		)
		self.assertFalse(
			frappe.db.exists(
				"Shop Rent Invoice",
				{"lease": lease.name, "docstatus": 1},
			)
		)

	def test_submit_generates_an_anchor_date_safe_monthly_schedule(self):
		lease = self._make_lease(
			start_date="2027-01-31",
			end_date="2027-03-31",
			first_payment_due_date="2027-01-31",
			monthly_rent_amount=1_250,
		)

		lease.submit()

		invoices = frappe.get_all(
			"Shop Rent Invoice",
			filters={"lease": lease.name},
			fields=[
				"docstatus",
				"airport",
				"shop",
				"tenant",
				"billing_month",
				"due_date",
				"amount_due",
			],
			order_by="due_date asc",
		)

		self.assertEqual(
			[str(invoice.due_date) for invoice in invoices],
			["2027-01-31", "2027-02-28", "2027-03-31"],
		)
		self.assertEqual(
			[str(invoice.billing_month) for invoice in invoices],
			["2027-01-01", "2027-02-01", "2027-03-01"],
		)
		for invoice in invoices:
			self.assertEqual(invoice.docstatus, 1)
			self.assertEqual(invoice.airport, self.airport.name)
			self.assertEqual(invoice.shop, self.shop.name)
			self.assertEqual(invoice.tenant, self.tenant.name)
			self.assertEqual(invoice.amount_due, 1_250)

		generate_rent_invoices(lease)
		self.assertEqual(
			frappe.db.count("Shop Rent Invoice", {"lease": lease.name}),
			3,
		)

	def test_future_lease_reserves_shop(self):
		lease = self._make_lease(
			start_date=add_days(today(), 10),
			end_date=add_days(today(), 40),
			first_payment_due_date=add_days(today(), 10),
		)

		lease.submit()

		self.assertEqual(lease.status, "Upcoming")
		self.assertEqual(
			frappe.db.get_value("Airport Shop", self.shop.name, "status"), "Occupied"
		)

	def test_expired_lease_does_not_occupy_shop(self):
		lease = self._make_lease(
			start_date=add_days(today(), -40),
			end_date=add_days(today(), -10),
			first_payment_due_date=add_days(today(), -40),
		)

		lease.submit()

		self.assertEqual(lease.status, "Expired")
		self.assertEqual(
			frappe.db.get_value("Airport Shop", self.shop.name, "status"), "Available"
		)

	def test_overlapping_submitted_lease_is_rejected(self):
		first_lease = self._make_lease(
			start_date=today(),
			end_date=add_days(today(), 30),
			first_payment_due_date=today(),
		)
		first_lease.submit()

		overlapping_lease = self._make_lease(
			start_date=add_days(today(), 15),
			end_date=add_days(today(), 45),
			first_payment_due_date=add_days(today(), 15),
		)

		with self.assertRaises(frappe.ValidationError):
			overlapping_lease.submit()

	def test_negotiated_rent_is_not_overwritten_by_shop_rent(self):
		lease = self._make_lease(
			start_date=today(),
			end_date=add_days(today(), 30),
			first_payment_due_date=today(),
			monthly_rent_amount=1_250,
		)

		self.assertEqual(lease.monthly_rent_amount, 1_250)

	def test_invalid_dates_are_rejected(self):
		with self.assertRaises(frappe.ValidationError):
			self._make_lease(
				start_date=add_days(today(), 10),
				end_date=today(),
				first_payment_due_date=today(),
			)

		with self.assertRaises(frappe.ValidationError):
			self._make_lease(
				start_date=today(),
				end_date=add_days(today(), 30),
				first_payment_due_date=add_days(today(), 31),
			)

		with self.assertRaises(frappe.ValidationError):
			self._make_lease(
				start_date=today(),
				end_date=add_days(today(), 30),
				first_payment_due_date=today(),
				monthly_rent_amount=-1,
			)

	def _make_airport(self, unique_id):
		return frappe.get_doc(
			{
				"doctype": "Airport",
				"code": unique_id.upper(),
				"city": "Test City",
				"country": "Test Country",
			}
		).insert(set_name=f"Test Airport {unique_id}")

	def _make_lease(
		self, start_date, end_date, first_payment_due_date, monthly_rent_amount=1_500
	):
		return frappe.get_doc(
			{
				"doctype": "Shop Lease",
				"shop": self.shop.name,
				"tenant": self.tenant.name,
				"start_date": start_date,
				"end_date": end_date,
				"first_payment_due_date": first_payment_due_date,
				"monthly_rent_amount": monthly_rent_amount,
			}
		).insert()
