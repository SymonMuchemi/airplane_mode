// Copyright (c) 2026, SymonMuchemi and contributors
// For license information, please see license.txt

frappe.ui.form.on("Airplane Flight", {
	refresh(frm) {
		frm.add_custom_button(
			__("Assign Gate"),
			function () {
				const dialog = new frappe.ui.Dialog({
					title: __("Select Gate"),
					fields: [
						{
							label: "Gate Number",
							fieldname: "gate",
							fieldtype: "Data",
						},
					],
					size: "small",
					primary_action_label: "Assign",
					primary_action(values) {
						frm.set_value("gate", values.gate);
						dialog.hide();
					},
				});

				dialog.show();
			},
			__("Actions")
		);
	},
});
