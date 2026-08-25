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
		}
	},
});
