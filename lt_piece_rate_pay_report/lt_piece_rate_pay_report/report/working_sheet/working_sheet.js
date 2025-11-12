// Copyright (c) 2025, LTL and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Working Sheet"] = {
	"filters": [
		 {
            "fieldname": "contract_worker_payroll_entry",
            "label": __("Contract Worker Payroll Entry"),
            "fieldtype": "Link",
            "options": "Contract Worker Payroll Entry",
            "reqd": 1
        },
		 {
            "fieldname": "start_date",
            "label": __("Start Date"),
            "fieldtype": "Date",
            "read_only": 1
        },
        {
            "fieldname": "end_date",
            "label": __("End Date"),
            "fieldtype": "Date",
            "read_only": 1
        },
		{
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
	,
	 onload: function(report) {
        report.page.fields_dict.contract_worker_payroll_entry.df.onchange = () => {
            let selected = report.get_filter_value("contract_worker_payroll_entry");

            if (!selected) return;

            frappe.db.get_doc("Contract Worker Payroll Entry", selected).then(doc => {
                report.set_filter_value("start_date", doc.start_date);
                report.set_filter_value("end_date", doc.end_date);
            });
        };
    }
       
};
