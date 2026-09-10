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
	refresh(frm) {
		frm.add_custom_button("Tenant", async () => {
			let tenants = await frappe.db.get_list(
				"Shop Lease",
				(filters = { shop: frm.doc.name }),
				// (field = ["tenant"]),
			);
			
			console.log("Tenants: ", tenants);
		});
	},
});
