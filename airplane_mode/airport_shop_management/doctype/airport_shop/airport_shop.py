# Copyright (c) 2026, SymonMuchemi and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class AirportShop(Document):
	def validate(self):
		self._set_default_rent_amount()
		self._validate_positive_values()
		self._validate_unique_shop_number_for_airport()

	def _set_default_rent_amount(self):
		if flt(self.monthly_rent_amount) > 0:
			return

		self.monthly_rent_amount = flt(
			frappe.get_single_value("Airport Shop Settings", "default_rent_amount")
		)

	def _validate_positive_values(self):
		if flt(self.area) <= 0:
			frappe.throw(_("Shop area must be greater than zero."))

		if flt(self.monthly_rent_amount) <= 0:
			frappe.throw(_("Monthly rent amount must be greater than zero."))

	def _validate_unique_shop_number_for_airport(self):
		if not self.airport or not self.shop_number:
			return

		filters = {
			"airport": self.airport,
			"shop_number": self.shop_number,
		}
		if self.name:
			filters["name"] = ("!=", self.name)

		if frappe.db.exists("Airport Shop", filters):
			frappe.throw(
				_("Shop number {0} already exists at airport {1}.").format(
					frappe.bold(self.shop_number), frappe.bold(self.airport)
				)
			)
