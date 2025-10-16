# Copyright (c) 2025, Lithe-Tech LTD and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):

	if not filters:
		filters = {}

	columns = get_columns()
	data = get_data(filters)
	
	return columns, data

def get_columns():
	return [
        _("Process Type") + ":Data:90",
        _("Buyer") + ":Data:200",
        _("Po") + ":Data:200",
        _("Style") + ":Data:90",
        # _("Sales Contract") + ":Data:200",
        _("Bill Qty (pcs)") + ":Int:100",
        _("Bill Qty(Dzn)") + ":Float:100",
		_("Pcs Rate") + ":Float:100",
		_("Bill") + ":Float:100",

        _("Stamp Deduct") + ":Int:100",
		_("Total Bill") + "Int:100"

    ]

def get_data(filters):

	conditions, filters = get_conditions(filters)


	result = frappe.db.sql("""SELECT
	ppi.process_type,
    ppi.buyer,
    ppi.po,
	ppi.style,
    SUM(ppi.quantity),
	SUM(ppi.quantitydz),
	SUM(ppi.quantitydz*ppi.rate)/SUM(ppi.quantitydz),
						
    SUM(ppi.quantitydz*ppi.rate),
	0,
	SUM(ppi.quantitydz)*ppi.rate-0					
	 FROM
            `tabContract Worker Salary Slip` cwss
            JOIN `tabProduction Pay Items` ppi ON cwss.name = ppi.parent
	where
		 %s
	GROUP BY
		ppi.buyer, ppi.po, ppi.process_type, ppi.style
						
""" 
	% conditions, as_list=1)

	return result

def get_conditions(filters):
	conditions="" 
	if filters.get("contract_worker_payroll_entry"): conditions += "cwss.contract_worker_payroll_entry= '%s'" % filters["contract_worker_payroll_entry"]
	if filters.get("employee_type"): conditions += "and cwss.employee_type= '%s'" % filters["employee_type"]

	return conditions, filters