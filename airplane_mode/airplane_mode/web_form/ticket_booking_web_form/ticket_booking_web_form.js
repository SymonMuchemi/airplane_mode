frappe.ready(function () {
	const params = new URLSearchParams(window.location.search);
	const flight = params.get("flight");

	if (flight) {
		frappe.web_form.set_value("flight", flight);
		frappe.web_form.set_value("flight_price", 1000);
	}
});
