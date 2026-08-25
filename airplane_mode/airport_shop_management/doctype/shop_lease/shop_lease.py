# Copyright (c) 2026, SymonMuchemi and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_months, flt, get_first_day, getdate, nowdate


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
		generate_rent_invoices(self)
		update_shop_occupancy(self.shop)

	def before_cancel(self):
		self._lock_shop()
		self._validate_no_submitted_payments()
		self.status = "Cancelled"

	def on_cancel(self):
		cancel_rent_invoices(self.name)
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

	def _validate_no_submitted_payments(self):
		submitted_payment = frappe.db.exists(
			"Shop Rent Payment",
			{"lease": self.name, "docstatus": 1},
		)
		if submitted_payment:
			frappe.throw(
				_("Cancel payment {0} before cancelling this lease.").format(
					frappe.get_desk_link("Shop Rent Payment", submitted_payment)
				)
			)


def generate_rent_invoices(lease):
	"""Create one submitted rent invoice for each monthly due date."""
	frappe.db.get_value("Shop Lease", lease.name, "name", for_update=True)

	first_due_date = getdate(lease.first_payment_due_date)
	end_date = getdate(lease.end_date)
	month_offset = 0

	while True:
		due_date = getdate(add_months(first_due_date, month_offset))
		if due_date > end_date:
			break

		billing_month = getdate(get_first_day(due_date))
		existing_invoice = frappe.db.get_value(
			"Shop Rent Invoice",
			{
				"lease": lease.name,
				"billing_month": billing_month,
				"docstatus": ("<", 2),
			},
			["name", "docstatus", "due_date", "amount_due"],
			as_dict=True,
		)

		if existing_invoice:
			_validate_existing_invoice(existing_invoice, lease, due_date)
			if existing_invoice.docstatus == 0:
				invoice = frappe.get_doc("Shop Rent Invoice", existing_invoice.name)
				invoice.flags.ignore_permissions = True
				invoice.submit()
		else:
			invoice = frappe.get_doc(
				{
					"doctype": "Shop Rent Invoice",
					"lease": lease.name,
					"billing_month": billing_month,
					"due_date": due_date,
					"amount_due": lease.monthly_rent_amount,
				}
			)
			invoice.insert(ignore_permissions=True)
			invoice.submit()

		month_offset += 1


def _validate_existing_invoice(invoice, lease, due_date):
	precision = frappe.get_precision("Shop Rent Invoice", "amount_due")
	if getdate(invoice.due_date) != due_date or flt(invoice.amount_due, precision) != flt(
		lease.monthly_rent_amount, precision
	):
		frappe.throw(
			_("Existing rent invoice {0} does not match the lease payment schedule.").format(
				frappe.get_desk_link("Shop Rent Invoice", invoice.name)
			)
		)


def cancel_rent_invoices(lease):
	for invoice_name in frappe.get_all(
		"Shop Rent Invoice",
		filters={"lease": lease, "docstatus": 1},
		pluck="name",
	):
		invoice = frappe.get_doc("Shop Rent Invoice", invoice_name)
		invoice.flags.ignore_permissions = True
		invoice.cancel()


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
