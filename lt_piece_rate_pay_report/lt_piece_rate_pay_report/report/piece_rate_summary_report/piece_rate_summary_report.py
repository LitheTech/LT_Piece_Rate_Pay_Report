import frappe

def execute(filters=None):
    if not filters:
        filters = {}

    columns = get_columns()
    data = get_data(filters)

    return columns, data


def get_columns():
    return [
        {"label": "Employee", "fieldname": "employee", "fieldtype": "Data", "width": 120},
        {"label": "Employee Name", "fieldname": "employee_name", "fieldtype": "Data", "width": 180},
        # {"label": "Total Pieces", "fieldname": "total_pieces", "fieldtype": "Float", "width": 120},
        # {"label": "Total Dozen", "fieldname": "total_dozen", "fieldtype": "Float", "width": 120},
        {"label": "Amount Payable", "fieldname": "amount_payable", "fieldtype": "Currency", "width": 150},
        {"label": "Stamp Deduction", "fieldname": "stamp_ded", "fieldtype": "Currency", "width": 150},
        {"label": "Net Amount", "fieldname": "net_amount", "fieldtype": "Currency", "width": 150},
        {"label": "Advance", "fieldname": "advance", "fieldtype": "Currency", "width": 150},
        {"label": "Payable After Deduct", "fieldname": "payable_after_deduct", "fieldtype": "Currency", "width": 150},

    ]


def get_data(filters):
    conditions = ""
    if filters.get("contract_worker_payroll_entry"):
        # conditions["contract_worker_payroll_entry"] = filters.get("contract_worker_payroll_entry")
        conditions += " contract_worker_payroll_entry= '%s'" % filters["contract_worker_payroll_entry"]


    slips = frappe.db.sql("""
    SELECT 
        employee, 
        employee_name, 
        
        total_amount AS amount_payable,
        10 as stamp_ded,
        total_amount-10 AS net_amount,
        0 as advance,
        total_amount-10-0 As payable_after_deduct
                                          
    FROM `tabContract Worker Salary Slip`
    WHERE %s and total_amount>0
	"""%conditions, as_dict=True)


    return slips
