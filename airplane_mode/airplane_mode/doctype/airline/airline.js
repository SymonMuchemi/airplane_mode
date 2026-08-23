// Copyright (c) 2026, SymonMuchemi and contributors
// For license information, please see license.txt

frappe.ui.form.on("Airline", {
	refresh(frm) {
		const airline_website_link = frm.doc.website;
		if (frm.doc.website) {
			frm.add_web_link(airline_website_link, "Visit Website");
		}
	},
});
