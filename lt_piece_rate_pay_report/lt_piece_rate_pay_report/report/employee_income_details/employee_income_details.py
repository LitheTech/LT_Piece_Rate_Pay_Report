# Copyright (c) 2026, LTL and contributors
# For license information, please see license.txt

import frappe



def execute(filters=None):
    if not filters:
        filters = {}

    columns = get_columns()
    data = get_data(filters)

    return columns, data


def get_columns():
    return [
        {"label": "Employee", "fieldname": "employee", "fieldtype": "Data", "width": 140},
        {"label": "Employee Type", "fieldname": "employee_type", "fieldtype": "Data", "width": 130},
        {"label": "Week Wage Detail", "fieldname": "payroll", "fieldtype": "Link","options":"Contract Worker Salary Slip", "width": 140},
        {"label": "From Date", "fieldname": "from_date", "fieldtype": "Date", "width": 110},
        {"label": "To Date", "fieldname": "to_date", "fieldtype": "Date", "width": 110},
        {"label": "Total Amount", "fieldname": "total_amount", "fieldtype": "Currency", "width": 130},
    ]


def get_data(filters):
    conditions, filters = get_conditions(filters)

    data = frappe.db.sql("""
    SELECT 
    cwss.employee,
    cwss.employee_type,
    cwss.name AS payroll,
    cwss.from_date AS from_date,
    cwss.to_date AS to_date,
    COALESCE((cwss.total_amount), 0) AS total_amount
    FROM 
        `tabContract Worker Salary Slip` cwss
    WHERE %s and cwss.total_amount>0
    ORDER BY 
        cwss.employee ASC;
    """%conditions, as_dict=True)

    return data


def get_conditions(filters):
    conditions = ""

    if filters.get("from_date"):
        conditions += " cwss.from_date >= '%s'" % filters["from_date"]
    if filters.get("to_date"):
        conditions += " AND cwss.to_date <= '%s'" % filters["to_date"]

    if filters.get("employee"):
        conditions += " AND cwss.employee = '%s'" % filters["employee"]
    if filters.get("employee_type"):
        conditions += " AND cwss.employee_type = '%s'" % filters["employee_type"]
    if filters.get("payroll"):
        conditions += " AND cwss.contract_worker_payroll_entry = '%s'" % filters["payroll"]

    return conditions, filters