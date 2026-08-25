// Copyright (c) 2026, SymonMuchemi and contributors
// For license information, please see license.txt

frappe.ui.form.on("Airplane Ticket", {
	refresh(frm) {
		frm.add_custom_button(
			__("Assign Seat"),
			function () {
				const dialog = new frappe.ui.Dialog({
					title: __("Select Seat"),
					fields: [
						{
							label: "Seat Number",
							fieldname: "seat_number",
							fieldtype: "Data",
						},
					],
					size: "small",
					primary_action_label: "Assign",
					primary_action(values) {
						frm.set_value("seat", values.seat_number);
						dialog.hide();
					},
				});

				dialog.show();
			},
			__("Actions"),
		);
	},
});
