# Copyright (c) 2026, SymonMuchemi and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, get_first_day, getdate, nowdate


class ShopRentInvoice(Document):
	def validate(self):
		lease = self._get_submitted_lease()
		self._set_lease_snapshot(lease)
		self._validate_billing_period(lease)
		self._validate_amount_due()
		self._validate_unique_billing_month()
		self._set_payment_totals(paid_amount=0)

		if self.is_new():
			self.last_reminder_sent_on = None

	def before_update_after_submit(self):
		self._set_payment_totals(get_submitted_payment_total(self.name))

	def before_cancel(self):
		frappe.db.get_value("Shop Rent Invoice", self.name, "name", for_update=True)
		submitted_payment = frappe.db.exists(
			"Shop Rent Payment",
			{"rent_invoice": self.name, "docstatus": 1},
		)
		if submitted_payment:
			frappe.throw(
				_("Cancel payment {0} before cancelling this rent invoice.").format(
					frappe.get_desk_link("Shop Rent Payment", submitted_payment)
				)
			)

		self.status = "Cancelled"

	def _get_submitted_lease(self):
		lease = frappe.db.get_value(
			"Shop Lease",
			self.lease,
			[
				"name",
				"docstatus",
				"airport",
				"shop",
				"tenant",
				"start_date",
				"end_date",
				"monthly_rent_amount",
			],
			as_dict=True,
			for_update=True,
		)

		if not lease or lease.docstatus != 1:
			frappe.throw(_("Rent invoices can only be created for a submitted lease."))

		return lease

	def _set_lease_snapshot(self, lease):
		self.airport = lease.airport
		self.shop = lease.shop
		self.tenant = lease.tenant
		self.amount_due = lease.monthly_rent_amount

		if self.billing_month:
			self.billing_month = get_first_day(self.billing_month)

	def _validate_billing_period(self, lease):
		if not self.billing_month or not self.due_date:
			return

		billing_month = getdate(self.billing_month)
		due_date = getdate(self.due_date)
		start_date = getdate(lease.start_date)
		end_date = getdate(lease.end_date)

		if not start_date <= due_date <= end_date:
			frappe.throw(_("Invoice due date must fall within the lease period."))

		if getdate(get_first_day(due_date)) != billing_month:
			frappe.throw(_("Billing month must match the month of the invoice due date."))

	def _validate_amount_due(self):
		if flt(self.amount_due) <= 0:
			frappe.throw(_("Invoice amount must be greater than zero."))

	def _validate_unique_billing_month(self):
		if not self.lease or not self.billing_month:
			return

		filters = {
			"lease": self.lease,
			"billing_month": self.billing_month,
			"docstatus": ("<", 2),
		}
		if self.name:
			filters["name"] = ("!=", self.name)

		duplicate_invoice = frappe.db.exists("Shop Rent Invoice", filters)
		if duplicate_invoice:
			frappe.throw(
				_("A rent invoice already exists for this lease and billing month: {0}.").format(
					frappe.get_desk_link("Shop Rent Invoice", duplicate_invoice)
				)
			)

	def _set_payment_totals(self, paid_amount):
		paid_amount, outstanding_amount, status = get_invoice_payment_state(
			self.amount_due,
			paid_amount,
			self.due_date,
		)
		self.paid_amount = paid_amount
		self.outstanding_amount = outstanding_amount
		self.status = status


def get_submitted_payment_total(rent_invoice, exclude_payment=None):
	filters = {
		"rent_invoice": rent_invoice,
		"docstatus": 1,
	}
	if exclude_payment:
		filters["name"] = ("!=", exclude_payment)

	return sum(
		flt(amount)
		for amount in frappe.get_all(
			"Shop Rent Payment",
			filters=filters,
			pluck="amount_paid",
		)
	)


def get_invoice_payment_state(amount_due, paid_amount, due_date):
	precision = frappe.get_precision("Shop Rent Invoice", "amount_due")
	amount_due = flt(amount_due, precision)
	paid_amount = flt(paid_amount, precision)
	outstanding_amount = flt(max(amount_due - paid_amount, 0), precision)

	if outstanding_amount == 0:
		status = "Paid"
	elif paid_amount > 0:
		status = "Partly Paid"
	elif due_date and getdate(due_date) < getdate(nowdate()):
		status = "Overdue"
	else:
		status = "Unpaid"

	return paid_amount, outstanding_amount, status


def recalculate_invoice(rent_invoice):
	invoice = frappe.db.get_value(
		"Shop Rent Invoice",
		rent_invoice,
		["name", "docstatus", "amount_due", "due_date"],
		as_dict=True,
		for_update=True,
	)
	if not invoice or invoice.docstatus != 1:
		frappe.throw(_("Payments can only update a submitted rent invoice."))

	paid_amount, outstanding_amount, status = get_invoice_payment_state(
		invoice.amount_due,
		get_submitted_payment_total(rent_invoice),
		invoice.due_date,
	)
	frappe.db.set_value(
		"Shop Rent Invoice",
		rent_invoice,
		{
			"paid_amount": paid_amount,
			"outstanding_amount": outstanding_amount,
			"status": status,
		},
	)
