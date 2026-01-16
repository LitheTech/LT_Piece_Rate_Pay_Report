// Copyright (c) 2026, LTL and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Production Status Report"] = {
	"filters": [
		{
            "fieldname": "po_list",
            "label": __("PO List"),
            "fieldtype": "Link",
            "options": "PO List",
            // "reqd": 1
        },
		{
            "fieldname": "style_list",
            "label": __("Style List"),
            "fieldtype": "Link",
            "options": "Style List",
            // "reqd": 1
        },
		{
            "fieldname": "color",
            "label": __("Color"),
            "fieldtype": "Data"
        }
	]
};


