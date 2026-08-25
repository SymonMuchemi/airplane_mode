# Copyright (c) 2026, SymonMuchemi and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate, nowdate

from airplane_mode.airport_shop_management.doctype.shop_rent_invoice.shop_rent_invoice import (
	get_submitted_payment_total,
	recalculate_invoice,
)


class ShopRentPayment(Document):
	def validate(self):
		invoice = self._get_submitted_invoice()
		self._set_invoice_snapshot(invoice)
		self._validate_payment_details()

	def before_submit(self):
		invoice = self._get_submitted_invoice(for_update=True)
		paid_amount = get_submitted_payment_total(
			self.rent_invoice,
			exclude_payment=self.name,
		)
		precision = frappe.get_precision("Shop Rent Invoice", "amount_due")
		outstanding_amount = flt(invoice.amount_due - paid_amount, precision)

		if flt(self.amount_paid, precision) > outstanding_amount:
			frappe.throw(
				_("Payment amount cannot exceed the outstanding amount of {0}.").format(
					frappe.format_value(
						outstanding_amount,
						{"fieldtype": "Currency"},
					)
				)
			)

	def on_submit(self):
		recalculate_invoice(self.rent_invoice)

	def before_cancel(self):
		self._get_submitted_invoice(for_update=True)

	def on_cancel(self):
		recalculate_invoice(self.rent_invoice)

	def _get_submitted_invoice(self, for_update=False):
		invoice = frappe.db.get_value(
			"Shop Rent Invoice",
			self.rent_invoice,
			[
				"name",
				"docstatus",
				"lease",
				"airport",
				"shop",
				"tenant",
				"billing_month",
				"amount_due",
			],
			as_dict=True,
			for_update=for_update,
		)

		if not invoice or invoice.docstatus != 1:
			frappe.throw(_("Payments can only be made against a submitted rent invoice."))

		return invoice

	def _set_invoice_snapshot(self, invoice):
		self.lease = invoice.lease
		self.airport = invoice.airport
		self.shop = invoice.shop
		self.tenant = invoice.tenant
		self.billing_month = invoice.billing_month

	def _validate_payment_details(self):
		if flt(self.amount_paid) <= 0:
			frappe.throw(_("Payment amount must be greater than zero."))

		if self.payment_date and getdate(self.payment_date) > getdate(nowdate()):
			frappe.throw(_("Payment date cannot be in the future."))

		if self.payment_method and self.payment_method != "Cash" and not self.reference_number:
			frappe.throw(_("Reference number is required for non-cash payments."))
