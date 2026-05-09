// Copyright (c) 2026, LTL and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Balance Status Report"] = {
	filters: [
		{
			"fieldname":"company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			// "default": frappe.defaults.get_user_default("Company"),
			// "reqd": 1
		},
		{
			fieldname: "buyer",
			label: __("Buyer"),
			fieldtype: "Link",
			options: "Buyer",
		},
		{
			fieldname: "sales_contract",
			label: __("	Sales Contract	"),
			fieldtype: "Link",
			options: "Sales Contract",
			get_query: function () {
				var buyer = frappe.query_report.get_filter_value("buyer");
				if (buyer) {
					return {
						filters: {
							buyer: buyer
						}
					};
				}
			},
		},
		{
			fieldname: "po_list",
			label: __("PO List"),
			fieldtype: "Link",
			options: "PO List",
			get_query: function () {
				var sales_contract = frappe.query_report.get_filter_value("sales_contract");
				if (sales_contract) {
					return {
						filters: {
							sales_contract: sales_contract
						}
					};
				}
			},
			// reqd: 1,

			on_change: function () {
				frappe.query_report.set_filter_value("style", "");
				frappe.query_report.set_filter_value("color", "");
				load_styles();   // ✅ FIX 1
				frappe.query_report.refresh();
			}
		},
		{
			fieldname: "style",
			label: __("Style"),
			fieldtype: "Select",
			on_change: function () {
				frappe.query_report.set_filter_value("color", "");
				load_colors();
				frappe.query_report.refresh();
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
			frappe.query_report.get_filter("style").df.options =
				["", ...(r.message || [])];
			frappe.query_report.get_filter("style").refresh();
		}
	});
}

function load_colors() {
	let po = frappe.query_report.get_filter_value("po_list");
	let style = frappe.query_report.get_filter_value("style");
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
