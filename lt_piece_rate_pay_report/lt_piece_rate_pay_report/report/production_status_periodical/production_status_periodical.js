// Copyright (c) 2026, LTL and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Production Status Periodical"] = {
	filters: [
		{
            "fieldname": "start_date",
            "label": __("Start Date"),
            "fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd": 1,
        },
        {
            "fieldname": "end_date",
            "label": __("End Date"),
            "fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd": 1,
        },
		{
			fieldname: "po_list",
			label: __("PO List"),
			fieldtype: "Link",
			options: "PO List",

			on_change: function () {
				// ✅ Reset dependent filters (value + options)
				reset_filter("style_list");
				reset_filter("color");

				// Load fresh styles
				load_styles();

				// Clear old report data
				frappe.query_report.refresh();
			}
		},
		{
			fieldname: "style_list",
			label: __("Style"),
			fieldtype: "Select",

			on_change: function () {
				// ✅ Reset color filter
				reset_filter("color");

				load_colors();

				// Refresh report
				frappe.query_report.refresh();
			}
		},
		{
			fieldname: "color",
			label: __("Color"),
			fieldtype: "Select"
		},
		{
			fieldname: "process_type",
			fieldtype: "Link",
			label: "Process Type",
			options: "Process Type"
		},
		{
			fieldname: "floor",
			fieldtype: "Link",
			label: "Floor",
			options: "Floor"
		},
		{
			fieldname: "line",
			fieldtype: "Link",
			label: "Line",
			options: "Facility or Line"
		},
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
		},
	]
};


// ---------------- COMMON RESET FUNCTION ----------------
function reset_filter(fieldname) {
	let filter = frappe.query_report.get_filter(fieldname);

	// Clear value
	frappe.query_report.set_filter_value(fieldname, "");

	// Clear options
	filter.df.options = [""];

	// Refresh UI
	filter.refresh();
}


// ---------------- LOAD STYLES ----------------
function load_styles() {
	let po = frappe.query_report.get_filter_value("po_list");
	if (!po) return;

	frappe.call({
		method: "lt_piece_rate_pay_report.lt_piece_rate_pay_report.report.production_status_periodical.production_status_periodical.get_styles",
		args: { po_list: po },

		callback: function (r) {
			let options = [""];

			if (r.message) {
				options = ["", ...r.message];
			}

			let filter = frappe.query_report.get_filter("style_list");
			filter.df.options = options;
			filter.refresh();

			// Ensure no old value remains
			frappe.query_report.set_filter_value("style_list", "");
		}
	});
}


// ---------------- LOAD COLORS ----------------
function load_colors() {
	let po = frappe.query_report.get_filter_value("po_list");
	let style = frappe.query_report.get_filter_value("style_list");

	if (!po || !style) return;

	frappe.call({
		method: "lt_piece_rate_pay_report.lt_piece_rate_pay_report.report.production_status_periodical.production_status_periodical.get_colors",
		args: {
			po_list: po,
			style: style
		},

		callback: function (r) {
			let options = [""];

			if (r.message) {
				options = ["", ...r.message];
			}

			let filter = frappe.query_report.get_filter("color");
			filter.df.options = options;
			filter.refresh();

			frappe.query_report.set_filter_value("color", "");
		}
	});
}