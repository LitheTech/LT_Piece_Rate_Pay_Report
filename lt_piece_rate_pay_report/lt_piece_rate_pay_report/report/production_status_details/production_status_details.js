// Copyright (c) 2026, LTL and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Production Status Details"] = {
	filters: [
		{
			fieldname: "po_list",
			label: __("PO List"),
			fieldtype: "Link",
			options: "PO List",
			reqd: 1,

			on_change: function () {
				frappe.query_report.set_filter_value("style_list", "");
				frappe.query_report.set_filter_value("color", "");
				load_styles();   // ✅ FIX 1
			}
		},
		{
			fieldname: "style_list",
			label: __("Style"),
			fieldtype: "Select",
			reqd: 1,
			on_change: function () {
				frappe.query_report.set_filter_value("color", "");
				load_colors();
			}
		},
		{
			fieldname: "color",
			label: __("Color"),
			fieldtype: "Select"
		},
		{
			"fieldname": "process_type",
			"fieldtype": "Link",
			"label": "Process Type",
			"mandatory": 0,
			"options": "Process Type",
			"wildcard_filter": 0
		},
		{
			"fieldname": "floor",
			"fieldtype": "Link",
			"label": "Floor",
			"mandatory": 0,
			"options": "Floor",
			"wildcard_filter": 0
		},
        {
			"fieldname": "line",
			"fieldtype": "Link",
			"label": "Line",
			"mandatory": 0,
			"options": "Facility or Line",
			"wildcard_filter": 0
		},
		{
			"fieldname":"company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"default": frappe.defaults.get_user_default("Company"),
		},
	]
};

// ---------------- FUNCTIONS ----------------

function load_styles() {
	let po = frappe.query_report.get_filter_value("po_list");
	if (!po) return;

	frappe.call({
		method: "lt_piece_rate_pay_report.lt_piece_rate_pay_report.report.production_status_details.production_status_details.get_styles",
		args: { po_list: po },
		callback: function (r) {
			frappe.query_report.get_filter("style_list").df.options =
				["", ...(r.message || [])];
			frappe.query_report.get_filter("style_list").refresh();
		}
	});
}

function load_colors() {
	let po = frappe.query_report.get_filter_value("po_list");
	let style = frappe.query_report.get_filter_value("style_list");
	if (!po || !style) return;

	frappe.call({
		method: "lt_piece_rate_pay_report.lt_piece_rate_pay_report.report.production_status_details.production_status_details.get_colors",
		args: {
			po_list: po,
			style: style
		},
		callback: function (r) {
			frappe.query_report.get_filter("color").df.options =
				["", ...(r.message || [])];
			frappe.query_report.get_filter("color").refresh();
		}
	});
}
