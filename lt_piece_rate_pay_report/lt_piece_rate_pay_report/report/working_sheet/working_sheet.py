import frappe


def execute(filters=None):
    if not filters:
        filters = {}

    columns, groups = get_columns(filters)
    data = get_data(groups, filters)

    return columns, data


# ------------------------------------
# GET COLUMNS
# ------------------------------------
def get_columns(filters):

    conditions, filters = get_conditions(filters)

    rows = frappe.db.sql(f"""
        SELECT 
            dp.name as dp_name,
            dp.sales_contract,
            dp.buyer,
            dp.po,
            dpc.style,
            dpc.color,
            dp.total_quantity,
            dp.completed_quantity,
            dp.bill_quantity,
            SUM(dpc.ongoing_quantity) as ongoing_qty
        FROM `tabDaily Production` dp
        LEFT JOIN `tabDaily Production Colors` dpc
            ON dpc.parent = dp.name
        WHERE dp.buyer IS NOT NULL
          AND dp.po IS NOT NULL
            AND dp.sales_contract IS NOT NULL
          AND {conditions} and dp.is_revised != 1
        GROUP BY dp.name, dpc.style, dpc.color
        ORDER BY dp.buyer
    """, as_dict=True)

    grouped = {}

    for r in rows:

        # 🔥 KEY CHANGE: dp.name is main grouping
        key = r.dp_name

        if key not in grouped:
            grouped[key] = {
                "buyer": r.buyer,
                "sales_contract":r.sales_contract,
                "po": r.po,
                "styles": set(),
                "colors": [],
                "total_qty": r.total_quantity or 0,
                "com_qty": r.completed_quantity or 0,
                "bill_qty": r.bill_quantity or 0,
            }



        if r.color:
            grouped[key]["colors"].append(
                f"{r.style}-{r.color} = {int(r.ongoing_qty or 0)} PCS"
            )

    groups = []

    for dp_name, val in grouped.items():

        color_string = " | ".join(val["colors"])

        groups.append((
            dp_name,
            val["buyer"],
            val["sales_contract"],
            val["po"],
            color_string,
            val["total_qty"],
            val["com_qty"],
            val["bill_qty"]
        ))

    # ----------------------------
    # COLUMNS
    # ----------------------------
    columns = [
        {"label": "Employee", "fieldname": "employee", "width": 120},
        {"label": "Employee Name", "fieldname": "employee_name", "width": 150},
    ]

    for dp_name, buyer,sales_contract, po, color_string, total_qty, com_qty, bill_qty in groups:

        scrubbed = frappe.scrub(f"{dp_name}")

        header = f"{buyer}^{sales_contract} $ {po} | {color_string}${total_qty}${com_qty}${bill_qty}"

        columns += [
            {"label": f"{header} $ Operation Name", "fieldname": f"{scrubbed}_operation", "fieldtype": "Small Text", "width": 140},
            {"label": f" $ Bill Qty", "fieldname": f"{scrubbed}_bill", "fieldtype": "Small Text", "width": 90},
            {"label": f" $ Qty Dzn", "fieldname": f"{scrubbed}_bill_dzn", "fieldtype": "Small Text", "width": 90},
            {"label": f" $ Rate Dzn", "fieldname": f"{scrubbed}_rate", "fieldtype": "Small Text", "width": 90},
            {"label": f" $ Total", "fieldname": f"{scrubbed}_total", "fieldtype": "Small Text", "width": 110},

            {"label": f"$ Bill Qty_num", "fieldname": f"{scrubbed}_bill_num", "fieldtype": "Integer", "width": 90},
            {"label": f"$ Bill Qty Dzn_num", "fieldname": f"{scrubbed}_bill_dzn_num", "fieldtype": "Integer", "width": 90},
            {"label": f" $ Total_num", "fieldname": f"{scrubbed}_total_num", "fieldtype": "Integer", "width": 110},
        ]

    return columns, groups


# ------------------------------------
# GET DATA
# ------------------------------------
def get_data(groups, filters):

    conditions, filters = get_conditions(filters)

    employees = frappe.db.sql(f"""
        SELECT DISTINCT 
            dpd.employee,
            dpd.employee_name
        FROM `tabDaily Production Details` dpd
        JOIN `tabDaily Production` dp ON dpd.parent = dp.name
        WHERE {conditions}
          AND dpd.employee IS NOT NULL
          ORDER BY dpd.employee_type ASC
    """, as_list=True)

    all_rows = frappe.db.sql(f"""
        SELECT 
            dpd.employee,
            dpd.employee_name,
            dpd.process_name,
            dp.name as dp_name,
            CAST(dpd.quantity AS SIGNED) AS quantity,
            dpd.quantity / 12 AS quantitydzn,
            dpd.rate,
            CAST(ROUND(dpd.amount) AS SIGNED) AS amount
        FROM `tabDaily Production` dp
        JOIN `tabDaily Production Details` dpd
            ON dp.name = dpd.parent
        WHERE {conditions} and dp.is_revised != 1
    """, as_dict=True)

    lookup = {}

    for r in all_rows:

        # 🔥 KEY FIX: dp.name
        key = (r.employee, r.dp_name)

        lookup.setdefault(key, []).append({
            "process_name": r.process_name,
            "quantity": r.quantity or 0,
            "quantitydzn": round(r.quantitydzn or 0, 1),
            "rate": r.rate or 0,
            "amount": round(r.amount or 0, 0),
        })

    data = []

    for emp, emp_name in employees:

        row = {
            "employee": emp,
            "employee_name": emp_name
        }

        for dp_name, buyer, po, *_ in groups:
            key = (emp, dp_name)
            processes = lookup.get(key, [])
            scrubbed = frappe.scrub(f"{dp_name}")

            op_html = []
            bill_html = []
            bill_dzn_html = []
            rate_html = []
            total_html = []

            for p in processes:
                p_name = str(p["process_name"] or "")
                
                # Check if process name is long (more than 5 characters)
                if len(p_name) > 15:
                    # 1. Remove the line-cell class for the long name so it wraps naturally
                    # or use a custom class that allows wrapping without a bottom border
                    op_html.append(f'<div class="line-cell">{p_name}</div>')
                    
                    # 2. Add the quantity and a filler &nbsp; to match the height of the wrapped text
                    bill_html.append(f'<div>{p["quantity"]}</div>')
                    bill_html.append('<div class="line-cell">&nbsp;</div>')
                    
                    bill_dzn_html.append(f'<div>{p["quantitydzn"]}</div>')
                    bill_dzn_html.append('<div class="line-cell">&nbsp;</div>')
                    
                    rate_html.append(f'<div>{p["rate"]}</div>')
                    rate_html.append('<div class="line-cell">&nbsp;</div>')
                    
                    total_html.append(f'<div>{p["amount"]}</div>')
                    total_html.append('<div class="line-cell">&nbsp;</div>')
                else:
                    # Normal behavior for short names
                    op_html.append(f'<div class="line-cell">{p_name}</div>')
                    bill_html.append(f'<div class="line-cell">{p["quantity"]}</div>')
                    bill_dzn_html.append(f'<div class="line-cell">{p["quantitydzn"]}</div>')
                    rate_html.append(f'<div class="line-cell">{p["rate"]}</div>')
                    total_html.append(f'<div class="line-cell">{p["amount"]}</div>')

            row[f"{scrubbed}_operation"] = "".join(op_html)
            row[f"{scrubbed}_bill"] = "".join(bill_html)
            row[f"{scrubbed}_bill_dzn"] = "".join(bill_dzn_html)
            row[f"{scrubbed}_rate"] = "".join(rate_html)
            row[f"{scrubbed}_total"] = "".join(total_html)

            row[f"{scrubbed}_bill_num"] = sum(p["quantity"] for p in processes)
            row[f"{scrubbed}_bill_dzn_num"] = sum(p["quantitydzn"] for p in processes)
            row[f"{scrubbed}_total_num"] = sum(p["amount"] for p in processes)

        data.append(row)

    return data


# ------------------------------------
# CONDITIONS
# ------------------------------------
def get_conditions(filters):

    conditions = "1=1"

    if filters.get("start_date") and filters.get("end_date"):
        conditions += " AND dp.production_date BETWEEN '%s' AND '%s'" % (
            filters["start_date"], filters["end_date"]
        )

    if filters.get("floor"):
        conditions += " AND dp.floor = '%s'" % filters["floor"]

    if filters.get("line"):
        conditions += " AND dp.facility_or_line = '%s'" % filters["line"]

    if filters.get("buyer"):
        conditions += " AND dp.buyer = '%s'" % filters["buyer"]

    if filters.get("process_type"):
        conditions += " AND dp.process_type = '%s'" % filters["process_type"]

    if filters.get("company"):
        conditions += " AND dp.company = '%s'" % filters["company"]

    return conditions, filters