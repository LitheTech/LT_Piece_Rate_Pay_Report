// Copyright (c) 2026, LTL
/* eslint-disable */

frappe.query_reports["Production Status Report"] = {
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
        }
    ]
};

// ---------------- FUNCTIONS ----------------

function load_styles() {
    let po = frappe.query_report.get_filter_value("po_list");
    if (!po) return;

    frappe.call({
        method: "lt_piece_rate_pay_report.lt_piece_rate_pay_report.report.production_status_report.production_status_report.get_styles",
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
        method: "lt_piece_rate_pay_report.lt_piece_rate_pay_report.report.production_status_report.production_status_report.get_colors",
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
