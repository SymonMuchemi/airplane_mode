// Copyright (c) 2026, SymonMuchemi and contributors
// For license information, please see license.txt

frappe.ui.form.on("Shop Rent Invoice", {
	refresh(frm) {
		if (frm.doc.docstatus === 1 && flt(frm.doc.outstanding_amount) > 0) {
			frm.add_custom_button(__("Record Payment"), () => {
				frappe.new_doc("Shop Rent Payment", {
					rent_invoice: frm.doc.name,
					payment_date: frappe.datetime.get_today(),
					amount_paid: frm.doc.outstanding_amount,
				});
			});

			if (!frm.doc.last_reminder_sent_on) {
				frm.add_custom_button(__("Send Rent Reminder"), () => {
					frappe.call({
						method:
							"airplane_mode.airport_shop_management.reminders.rent_reminder.send_rent_reminder",
						args: {
							invoice_name: frm.doc.name,
						},
						freeze: true,
						freeze_message: __("Queueing rent reminder..."),
						callback(response) {
							if (!response.exc) {
								frappe.show_alert({
									message: __("Rent reminder email queued"),
									indicator: "green",
								});
								frm.reload_doc();
							}
						},
					});
				});
			}
		}
	},
});
