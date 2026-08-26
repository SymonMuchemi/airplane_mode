// Copyright (c) 2026, SymonMuchemi and contributors
// For license information, please see license.txt

frappe.ui.form.on("Airport Shop", {
	setup(frm) {
		frm.set_query("type", () => {
			return {
				filters: {
					is_enabled: 1,
				},
			};
		});
	},
});
