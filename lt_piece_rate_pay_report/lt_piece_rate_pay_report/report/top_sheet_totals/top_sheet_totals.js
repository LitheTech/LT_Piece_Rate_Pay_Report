// Copyright (c) 2026, LTL and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Top Sheet Totals"] = {
		"filters": [
		 {
            "fieldname": "contract_worker_payroll_entry",
            "label": __("Contract Worker Payroll Entry"),
            "fieldtype": "Link",
            "options": "Contract Worker Payroll Entry",
            "reqd": 1
        },
        // {
        //     "fieldname": "company",
        //     "label": __("Company"),
        //     "fieldtype": "Link",
        //     "options": "Company"
        // },
        // {
        //     "fieldname": "from_date",
        //     "label": __("From Date"),
        //     "fieldtype": "Date"
        // },
        // {
        //     "fieldname": "to_date",
        //     "label": __("To Date"),
        //     "fieldtype": "Date"
        // }
        {
			"fieldname": "employee_type",
			"fieldtype": "Select",
			"label": "Employee Type",
			"mandatory": 0,
			// "default":"Active",
			// "options": "Active,Left",
			options: [
                '',
                'Salary',
                'Contract',
            ],
			"wildcard_filter": 0
		},{
			"fieldname": "buyer",
			"fieldtype": "Link",
			"label": "Buyer",
			"mandatory": 0,
			"options": "Buyer",
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
			"fieldname": "process_type",
			"fieldtype": "Link",
			"label": "Process Type",
			"mandatory": 0,
			"options": "Process Type",
			"wildcard_filter": 0
		},


	]
};
