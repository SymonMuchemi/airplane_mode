# Copyright (c) 2026, SymonMuchemi and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate, nowdate


class ShopLease(Document):
	def validate(self):
		self.status = "Draft"
		self._validate_lease_dates()
		self._validate_monthly_rent_amount()

	def before_submit(self):
		self._lock_shop()
		self._validate_no_overlapping_lease()
		self.status = self._get_status_for_today()

	def on_submit(self):
		update_shop_occupancy(self.shop)

	def before_cancel(self):
		self._lock_shop()
		self.status = "Cancelled"

	def on_cancel(self):
		update_shop_occupancy(self.shop)

	def _validate_lease_dates(self):
		if not self.start_date or not self.end_date:
			return

		start_date = getdate(self.start_date)
		end_date = getdate(self.end_date)

		if start_date > end_date:
			frappe.throw(_("Lease end date cannot be before its start date."))

		if not self.first_payment_due_date:
			return

		first_payment_due_date = getdate(self.first_payment_due_date)
		if not start_date <= first_payment_due_date <= end_date:
			frappe.throw(
				_("First payment due date must fall between the lease start and end dates.")
			)

	def _validate_monthly_rent_amount(self):
		if flt(self.monthly_rent_amount) <= 0:
			frappe.throw(_("Monthly rent amount must be greater than zero."))

	def _lock_shop(self):
		if self.shop:
			frappe.db.get_value("Airport Shop", self.shop, "name", for_update=True)

	def _validate_no_overlapping_lease(self):
		filters = {
			"shop": self.shop,
			"docstatus": 1,
			"start_date": ("<=", self.end_date),
			"end_date": (">=", self.start_date),
		}

		if self.name:
			filters["name"] = ("!=", self.name)

		overlapping_lease = frappe.db.exists("Shop Lease", filters)
		if overlapping_lease:
			frappe.throw(
				_("Shop {0} already has an overlapping lease: {1}.").format(
					frappe.bold(self.shop),
					frappe.get_desk_link("Shop Lease", overlapping_lease),
				)
			)

	def _get_status_for_today(self):
		today = getdate(nowdate())

		if getdate(self.end_date) < today:
			return "Expired"

		if getdate(self.start_date) > today:
			return "Upcoming"

		return "Active"


def update_shop_occupancy(shop):
	"""Set shop availability from all non-expired submitted leases."""
	if not shop:
		return

	is_occupied = frappe.db.exists(
		"Shop Lease",
		{
			"shop": shop,
			"docstatus": 1,
			"end_date": (">=", nowdate()),
		},
	)
	desired_status = "Occupied" if is_occupied else "Available"
	current_status = frappe.db.get_value("Airport Shop", shop, "status")

	if current_status != desired_status:
		frappe.db.set_value("Airport Shop", shop, "status", desired_status)
