# Copyright (c) 2026, SymonMuchemi and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import cint, flt, fmt_money, format_date, getdate, nowdate


def send_due_rent_reminders():
	"""Queue one reminder for every submitted monthly invoice that is due."""
	if not cint(
		frappe.get_single_value(
			"Airport Shop Settings",
			"enable_rent_reminders",
		)
	):
		return 0

	today = getdate(nowdate())
	invoice_names = frappe.get_all(
		"Shop Rent Invoice",
		filters={
			"docstatus": 1,
			"due_date": ("<=", today),
			"outstanding_amount": (">", 0),
			"last_reminder_sent_on": ("is", "not set"),
		},
		order_by="due_date asc, name asc",
		pluck="name",
	)

	queued_reminders = 0
	for index, invoice_name in enumerate(invoice_names):
		save_point = f"rent_reminder_{index}"
		frappe.db.savepoint(save_point)
		try:
			queued_reminders += int(
				_queue_rent_reminder(
					invoice_name,
					today,
					require_due_date=True,
				)
			)
		except Exception:
			frappe.db.rollback(save_point=save_point)
			frappe.db.release_savepoint(save_point)
			frappe.log_error(
				title=_("Rent reminder failed for {0}").format(invoice_name),
				message=frappe.get_traceback(),
				reference_doctype="Shop Rent Invoice",
				reference_name=invoice_name,
			)
		else:
			frappe.db.release_savepoint(save_point)

	return queued_reminders


@frappe.whitelist()
def send_rent_reminder(invoice_name):
	"""Queue a manual reminder for an unpaid submitted rent invoice."""
	invoice = frappe.get_doc("Shop Rent Invoice", invoice_name)
	invoice.check_permission("email")

	reminder_date = getdate(nowdate())
	queued = _queue_rent_reminder(
		invoice.name,
		reminder_date,
		require_due_date=False,
		raise_on_error=True,
	)
	if not queued:
		frappe.throw(_("The rent reminder could not be queued."))

	return {
		"invoice": invoice.name,
		"last_reminder_sent_on": reminder_date,
	}


def _queue_rent_reminder(
	invoice_name,
	today,
	*,
	require_due_date,
	raise_on_error=False,
):
	"""Lock and re-check an invoice before adding its reminder to Email Queue."""
	invoice = frappe.db.get_value(
		"Shop Rent Invoice",
		invoice_name,
		[
			"name",
			"docstatus",
			"tenant",
			"shop",
			"billing_month",
			"due_date",
			"outstanding_amount",
			"last_reminder_sent_on",
		],
		as_dict=True,
		for_update=True,
	)

	if not _is_eligible_for_reminder(invoice, today, require_due_date):
		if raise_on_error:
			_raise_ineligible_reminder(invoice, today, require_due_date)
		return False

	tenant = frappe.db.get_value(
		"Shop Tenant",
		invoice.tenant,
		["tenant_name", "email"],
		as_dict=True,
	)
	if not tenant or not tenant.email:
		message = _("Tenant {0} has no email address for rent invoice {1}.").format(
			invoice.tenant,
			invoice.name,
		)
		if raise_on_error:
			frappe.throw(message)

		frappe.log_error(
			title=_("Rent reminder recipient missing"),
			message=message,
			reference_doctype="Shop Rent Invoice",
			reference_name=invoice.name,
		)
		return False

	shop = frappe.db.get_value(
		"Airport Shop",
		invoice.shop,
		["shop_name", "shop_number"],
		as_dict=True,
	)
	shop_name = shop.shop_name if shop else invoice.shop
	shop_number = shop.shop_number if shop else ""

	email_queue = frappe.sendmail(
		recipients=[tenant.email],
		subject=_("Rent payment reminder for shop {0}").format(shop_name),
		template="rent_due_reminder",
		args={
			"tenant_name": tenant.tenant_name,
			"invoice_name": invoice.name,
			"shop_name": shop_name,
			"shop_number": shop_number,
			"billing_month": format_date(invoice.billing_month, "MMMM yyyy"),
			"due_date": format_date(invoice.due_date),
			"outstanding_amount": invoice.outstanding_amount,
			"formatted_outstanding_amount": fmt_money(invoice.outstanding_amount),
		},
		reference_doctype="Shop Rent Invoice",
		reference_name=invoice.name,
		add_unsubscribe_link=False,
	)
	if not email_queue:
		if raise_on_error:
			frappe.throw(_("The rent reminder could not be added to Email Queue."))
		return False

	frappe.db.set_value(
		"Shop Rent Invoice",
		invoice.name,
		"last_reminder_sent_on",
		today,
		update_modified=False,
	)
	return True


def _is_eligible_for_reminder(invoice, today, require_due_date):
	if not (
		invoice
		and invoice.docstatus == 1
		and invoice.due_date
		and flt(invoice.outstanding_amount) > 0
		and not invoice.last_reminder_sent_on
	):
		return False

	return not require_due_date or getdate(invoice.due_date) <= today


def _raise_ineligible_reminder(invoice, today, require_due_date):
	if not invoice:
		frappe.throw(_("The rent invoice no longer exists."))
	if invoice.docstatus != 1:
		frappe.throw(_("Rent reminders can only be sent for submitted invoices."))
	if invoice.last_reminder_sent_on:
		frappe.throw(
			_("A rent reminder was already sent on {0}.").format(
				format_date(invoice.last_reminder_sent_on)
			)
		)
	if flt(invoice.outstanding_amount) <= 0:
		frappe.throw(_("This invoice has no outstanding balance."))
	if require_due_date and (
		not invoice.due_date or getdate(invoice.due_date) > today
	):
		frappe.throw(_("This invoice is not due yet."))

	frappe.throw(_("The rent invoice is not eligible for a reminder."))
