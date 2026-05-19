import frappe
from frappe.utils import flt, money_in_words

def execute(filters=None):
    if not filters:
        filters = {}

    columns = get_columns()
    data = get_data(filters)

    total_payable = sum(flt(row.get("payable_after_deduct", 0)) for row in data)
    
    if data:
        # Add a special row for the words at the end of the data list
        data.append({
            "employee": "TOTAL_IN_WORDS", # We use this as a flag in HTML
            "employee_name": money_in_words(total_payable, "Taka = ")
        })

    return columns, data


def get_columns():
    return [
        {"label": "Employee ID", "fieldname": "employee", "fieldtype": "Data", "width": 120},
        {"label": "Employee Name", "fieldname": "employee_name", "fieldtype": "Data", "width": 180},
        {"label": "Total Qty", "fieldname": "total_pieces", "fieldtype": "Integer", "width": 120},
        # {"label": "Total Dozen", "fieldname": "total_dozen", "fieldtype": "Float", "width": 120},
        {"label": "Amount Payable", "fieldname": "amount_payable", "fieldtype": "Integer", "width": 150},
        {"label": "Stamp Deduction", "fieldname": "stamp_ded", "fieldtype": "Integer", "width": 150},
        {"label": "Net Amount", "fieldname": "net_amount", "fieldtype": "Integer", "width": 150},
        {"label": "Advance", "fieldname": "advance", "fieldtype": "Integer", "width": 150},
        {"label": "Payable After Deduct", "fieldname": "payable_after_deduct", "fieldtype": "Integer", "width": 150},
        {"label": "SIGNATURE", "fieldname": "singature", "fieldtype": "Data", "width": 150},

    ]


def get_data(filters):

    conditions, filters = get_conditions(filters)

    # conditions = ""
    # if filters.get("contract_worker_payroll_entry"):
    #     # conditions["contract_worker_payroll_entry"] = filters.get("contract_worker_payroll_entry")
    #     conditions += " contract_worker_payroll_entry= '%s'" % filters["contract_worker_payroll_entry"]


    slips = frappe.db.sql("""
        SELECT 
            cwss.employee, 
            cwss.employee_name, 
            cwss.total_pieces,
            cwss.total_amount AS amount_payable,
            ROUND(cwss.tax, 0) AS stamp_ded,
            ROUND(cwss.total_amount - cwss.tax, 0) AS net_amount,
            ROUND(cwss.advance, 0) AS advance,
            ROUND(cwss.total_amount - cwss.advance - cwss.tax, 0) AS payable_after_deduct
                                            
        FROM `tabContract Worker Salary Slip` cwss
        JOIN `tabProduction Pay Items` ppi ON cwss.name = ppi.parent
        WHERE %s AND total_amount > 0
        GROUP BY cwss.employee
    """ % conditions, as_dict=True)

    return slips


def get_conditions(filters):
    conditions = "1=1"

    if filters.get("contract_worker_payroll_entry"):
        conditions += " and cwss.contract_worker_payroll_entry= '%s'" % filters["contract_worker_payroll_entry"]

    if filters.get("employee_type"): 
        conditions += "and cwss.employee_type= '%s'" % filters["employee_type"]


    if filters.get("floor"):
        conditions += " AND ppi.floor = '%s'" % filters["floor"]

    if filters.get("line"):
        conditions += " AND ppi.line = '%s'" % filters["line"]

    if filters.get("buyer"):
        conditions += " AND ppi.buyer = '%s'" % filters["buyer"]
    
    # if filters.get("company"): conditions += " AND cwss.company = '%s'" % filters["company"]


    # if filters.get("process_type"):
    #     conditions += " AND ppi.process_type = '%s'" % filters["process_type"]

    # if filters.get("process"):
        # conditions += " AND dpd.process= '%s'" % filters["process"]

    return conditions, filters