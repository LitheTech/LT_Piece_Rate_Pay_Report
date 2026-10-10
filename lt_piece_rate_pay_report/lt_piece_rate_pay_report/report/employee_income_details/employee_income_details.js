// Copyright (c) 2026, LTL and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Employee Income Details"] = {
    "filters": [
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
            "reqd": 1
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.get_today(),
            "reqd": 1
        },
        {
            "fieldname": "employee",
            "label": __("Employee"),
            "fieldtype": "Link",
            "options": "Employee",
            "default": ""
        },
        {
            "fieldname": "employee_type",
            "label": __("Employee Type"),
            "fieldtype": "Link",
            "options": "Employment Type",
            "default": ""
        },
        {
            "fieldname": "payroll",
            "label": __("Payroll"),
            "fieldtype": "Link",
            "options": "Contract Worker Payroll Entry",
            "default": ""
        }
    ]
    
};