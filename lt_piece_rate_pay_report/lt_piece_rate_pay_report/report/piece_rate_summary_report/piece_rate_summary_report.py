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
        
        SUM(ppi.quantitydz*ppi.rate) AS amount_payable,
        cwss.tax as stamp_ded,
        SUM(ppi.quantitydz*ppi.rate)-cwss.tax AS net_amount,
        cwss.advance as advance,
        SUM(ppi.quantitydz*ppi.rate)-cwss.advance-cwss.tax As payable_after_deduct
                                          
    FROM
            `tabContract Worker Salary Slip` cwss
            JOIN `tabProduction Pay Items` ppi ON cwss.name = ppi.parent
    WHERE %s and total_amount>0
                          group by cwss.employee
	"""%conditions, as_dict=True)


    return slips


def get_conditions(filters):
    conditions = "1=1"

    if filters.get("contract_worker_payroll_entry"):
        conditions += " and cwss.contract_worker_payroll_entry= '%s'" % filters["contract_worker_payroll_entry"]

    if filters.get("floor"):
        conditions += " AND ppi.floor = '%s'" % filters["floor"]

    if filters.get("line"):
        conditions += " AND ppi.line = '%s'" % filters["line"]

    if filters.get("buyer"):
        conditions += " AND ppi.buyer = '%s'" % filters["buyer"]

    # if filters.get("process_type"):
    #     conditions += " AND ppi.process_type = '%s'" % filters["process_type"]

    # if filters.get("process"):
        # conditions += " AND dpd.process= '%s'" % filters["process"]

    return conditions, filters