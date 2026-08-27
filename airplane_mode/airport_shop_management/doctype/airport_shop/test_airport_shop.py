# Copyright (c) 2026, SymonMuchemi and Contributors
# See license.txt

from uuid import uuid4

import frappe
from frappe.tests import IntegrationTestCase


# On IntegrationTestCase, the doctype test records and all
# link-field test record dependencies are recursively loaded
# Use these module variables to add/remove to/from that list
EXTRA_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]
IGNORE_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]


class IntegrationTestAirportShop(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		unique_id = uuid4().hex[:8]
		self.shop_type = frappe.get_doc(
			{
				"doctype": "Shop Type",
				"type": f"Test Shop Type {unique_id}",
				"is_enabled": 1,
			}
		).insert()
		self.first_airport = self._make_airport(f"First {unique_id}", unique_id)
		self.second_airport = self._make_airport(f"Second {unique_id}", unique_id[::-1])

	def test_shop_number_is_unique_within_an_airport(self):
		shop_number = f"SHOP-{uuid4().hex[:8]}"
		self._make_shop(self.first_airport.name, shop_number)

		with self.assertRaises(frappe.ValidationError):
			self._make_shop(self.first_airport.name, shop_number)

		shop_at_another_airport = self._make_shop(self.second_airport.name, shop_number)
		self.assertEqual(shop_at_another_airport.shop_number, shop_number)

	def test_default_rent_is_copied_from_settings(self):
		with self.change_settings(
			"Airport Shop Settings", {"default_rent_amount": 1_750}
		):
			shop = self._make_shop(
				self.first_airport.name,
				f"SHOP-{uuid4().hex[:8]}",
				monthly_rent_amount=None,
			)

		self.assertEqual(shop.monthly_rent_amount, 1_750)

	def test_nonpositive_area_is_rejected(self):
		with self.assertRaises(frappe.ValidationError):
			self._make_shop(
				self.first_airport.name,
				f"SHOP-{uuid4().hex[:8]}",
				area=0,
			)

	def _make_airport(self, name, code):
		return frappe.get_doc(
			{
				"doctype": "Airport",
				"code": code.upper(),
				"city": "Test City",
				"country": "Test Country",
			}
		).insert(set_name=f"Test Airport {name}")

	def _make_shop(self, airport, shop_number, monthly_rent_amount=1_500, area=25):
		return frappe.get_doc(
			{
				"doctype": "Airport Shop",
				"airport": airport,
				"type": self.shop_type.name,
				"shop_number": shop_number,
				"shop_name": f"Test Shop {shop_number}",
				"monthly_rent_amount": monthly_rent_amount,
				"area": area,
				"area_unit": "Square Meters",
			}
		).insert()
