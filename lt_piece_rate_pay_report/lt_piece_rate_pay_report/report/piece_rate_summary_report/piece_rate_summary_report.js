// Copyright (c) 2025, Lithe-Tech LTD and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Piece Rate Summary Report"] = {
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
        // {
        //     "fieldname": "company",
        //     "label": __("Company"),
        //     "fieldtype": "Link",
        //     "options": "Company"
        // },
        

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
