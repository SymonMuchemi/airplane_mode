# Copyright (c) 2026, SymonMuchemi and contributors
# For license information, please see license.txt

from unittest.mock import patch
from uuid import uuid4

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, getdate, today
from frappe.utils.jinja import get_email_from_template

from airplane_mode.airport_shop_management.reminders.rent_reminder import (
	send_due_rent_reminders,
	send_rent_reminder,
)


class IntegrationTestRentReminder(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		unique_id = uuid4().hex[:8]
		self.shop_type = frappe.get_doc(
			{
				"doctype": "Shop Type",
				"type": f"Reminder Test {unique_id}",
				"is_enabled": 1,
			}
		).insert()
		self.airport = frappe.get_doc(
			{
				"doctype": "Airport",
				"code": unique_id.upper(),
				"city": "Test City",
				"country": "Test Country",
			}
		).insert(set_name=f"Reminder Test Airport {unique_id}")
		self.shop = frappe.get_doc(
			{
				"doctype": "Airport Shop",
				"airport": self.airport.name,
				"type": self.shop_type.name,
				"shop_number": f"REM-{unique_id}",
				"shop_name": f"Reminder Test Shop {unique_id}",
				"monthly_rent_amount": 1_500,
				"area": 25,
				"area_unit": "Square Meters",
			}
		).insert()
		self.tenant = frappe.get_doc(
			{
				"doctype": "Shop Tenant",
				"tenant_name": f"Reminder Test Tenant {unique_id}",
				"email": f"rent-reminder-{unique_id}@example.com",
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
		self.due_invoice = frappe.db.get_value(
			"Shop Rent Invoice",
			{"lease": self.lease.name, "due_date": today()},
			"name",
		)
		self.future_invoice = frappe.db.get_value(
			"Shop Rent Invoice",
			{
				"lease": self.lease.name,
				"due_date": (">", today()),
			},
			"name",
			order_by="due_date asc",
		)

	def test_due_invoice_is_queued_once_and_marked(self):
		self._set_reminders_enabled(True)

		with (
			patch(
				"airplane_mode.airport_shop_management.reminders.rent_reminder.frappe.get_all",
				return_value=[self.due_invoice, self.future_invoice],
			),
			patch(
				"airplane_mode.airport_shop_management.reminders.rent_reminder.frappe.sendmail",
				return_value=object(),
			) as sendmail,
		):
			self.assertEqual(send_due_rent_reminders(), 1)
			self.assertEqual(send_due_rent_reminders(), 0)

		sendmail.assert_called_once()
		mail = sendmail.call_args.kwargs
		self.assertEqual(mail["recipients"], [self.tenant.email])
		self.assertEqual(mail["template"], "rent_due_reminder")
		self.assertEqual(mail["reference_doctype"], "Shop Rent Invoice")
		self.assertEqual(mail["reference_name"], self.due_invoice)
		self.assertEqual(mail["args"]["outstanding_amount"], 1_500)
		last_reminder_sent_on = frappe.db.get_value(
			"Shop Rent Invoice",
			self.due_invoice,
			"last_reminder_sent_on",
		)
		self.assertIsNotNone(last_reminder_sent_on)
		self.assertEqual(
			getdate(last_reminder_sent_on),
			getdate(today()),
		)

	def test_disabled_reminders_do_not_queue_email(self):
		self._set_reminders_enabled(False)

		with (
			patch(
				"airplane_mode.airport_shop_management.reminders.rent_reminder.frappe.get_all"
			) as get_all,
			patch(
				"airplane_mode.airport_shop_management.reminders.rent_reminder.frappe.sendmail"
			) as sendmail,
		):
			self.assertEqual(send_due_rent_reminders(), 0)

		get_all.assert_not_called()
		sendmail.assert_not_called()
		self.assertIsNone(
			frappe.db.get_value(
				"Shop Rent Invoice",
				self.due_invoice,
				"last_reminder_sent_on",
			)
		)

	def test_scheduler_query_selects_due_invoice_but_not_future_invoice(self):
		self._set_reminders_enabled(True)

		with patch(
			"airplane_mode.airport_shop_management.reminders.rent_reminder._queue_rent_reminder",
			return_value=False,
		) as queue_rent_reminder:
			self.assertEqual(send_due_rent_reminders(), 0)

		selected_invoices = {
			call.args[0] for call in queue_rent_reminder.call_args_list
		}
		self.assertIn(self.due_invoice, selected_invoices)
		self.assertNotIn(self.future_invoice, selected_invoices)

	def test_paid_and_future_invoices_are_skipped(self):
		self._set_reminders_enabled(True)
		frappe.get_doc(
			{
				"doctype": "Shop Rent Payment",
				"rent_invoice": self.due_invoice,
				"payment_date": today(),
				"amount_paid": 1_500,
				"payment_method": "Cash",
			}
		).insert().submit()

		with (
			patch(
				"airplane_mode.airport_shop_management.reminders.rent_reminder.frappe.get_all",
				return_value=[self.due_invoice, self.future_invoice],
			),
			patch(
				"airplane_mode.airport_shop_management.reminders.rent_reminder.frappe.sendmail"
			) as sendmail,
		):
			self.assertEqual(send_due_rent_reminders(), 0)

		sendmail.assert_not_called()

	def test_failed_queue_attempt_is_not_marked_as_sent(self):
		self._set_reminders_enabled(True)

		with (
			patch(
				"airplane_mode.airport_shop_management.reminders.rent_reminder.frappe.get_all",
				return_value=[self.due_invoice],
			),
			patch(
				"airplane_mode.airport_shop_management.reminders.rent_reminder.frappe.sendmail",
				side_effect=RuntimeError("Email queue unavailable"),
			),
			patch(
				"airplane_mode.airport_shop_management.reminders.rent_reminder.frappe.log_error"
			) as log_error,
		):
			self.assertEqual(send_due_rent_reminders(), 0)

		log_error.assert_called_once()
		self.assertIsNone(
			frappe.db.get_value(
				"Shop Rent Invoice",
				self.due_invoice,
				"last_reminder_sent_on",
			)
		)

	def test_manual_reminder_queues_future_invoice_only_once(self):
		with patch(
			"airplane_mode.airport_shop_management.reminders.rent_reminder.frappe.sendmail",
			return_value=object(),
		) as sendmail:
			result = send_rent_reminder(self.future_invoice)
			with self.assertRaises(frappe.ValidationError):
				send_rent_reminder(self.future_invoice)

		sendmail.assert_called_once()
		self.assertEqual(result["invoice"], self.future_invoice)
		self.assertEqual(
			frappe.db.get_value(
				"Shop Rent Invoice",
				self.future_invoice,
				"last_reminder_sent_on",
			),
			getdate(today()),
		)

	def test_email_template_escapes_document_values(self):
		message, _text_content = get_email_from_template(
			"rent_due_reminder",
			{
				"tenant_name": "<script>alert('tenant')</script>",
				"invoice_name": "<INV&1>",
				"shop_name": "Shop & Sons",
				"shop_number": "<A-1>",
				"billing_month": "August 2026",
				"due_date": "27-08-2026",
				"formatted_outstanding_amount": "1,500.00",
			},
		)

		self.assertNotIn("<script>", message)
		self.assertIn("&lt;script&gt;", message)
		self.assertIn("&lt;INV&amp;1&gt;", message)
		self.assertIn("Shop &amp; Sons", message)
		self.assertIn("&lt;A-1&gt;", message)
		self.assertIn("1,500.00", message)

	def _set_reminders_enabled(self, enabled):
		settings = frappe.get_doc("Airport Shop Settings")
		settings.default_rent_amount = settings.default_rent_amount or 1_500
		settings.enable_rent_reminders = enabled
		settings.save(ignore_permissions=True)
