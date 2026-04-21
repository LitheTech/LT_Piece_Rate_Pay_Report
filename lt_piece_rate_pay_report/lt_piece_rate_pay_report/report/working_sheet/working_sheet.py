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
            dp.buyer, dp.po, dp.style_list,
            dpc.color,
            dp.total_quantity, dp.completed_quantity, dp.bill_quantity,
            SUM(dpc.ongoing_quantity) as ongoing_qty
        FROM `tabDaily Production` dp
        LEFT JOIN `tabDaily Production Colors` dpc 
            ON dpc.parent = dp.name
        WHERE dp.buyer IS NOT NULL
          AND dp.po IS NOT NULL
          AND dp.style_list IS NOT NULL
          AND {conditions}
        GROUP BY dp.buyer, dp.po, dp.style_list, dpc.color
        ORDER BY dp.buyer
    """, as_dict=True)

    # ✅ FIXED GROUPING
    grouped = {}

    for r in rows:
        key = (r.buyer, r.po, r.style_list)

        if key not in grouped:
            grouped[key] = {
                "colors": [],
                "total_qty": r.total_quantity or 0,
                "com_qty": r.completed_quantity or 0,
                "bill_qty": r.bill_quantity or 0,
            }

        if r.color:
            grouped[key]["colors"].append(
                f"{r.color} = {int(r.ongoing_qty or 0)} PCS"
            )

    # ✅ CONVERT TO LIST (WITH TOTALS)
    groups = []
    for (buyer, po, style), val in grouped.items():
        color_string = " | ".join(val["colors"])

        groups.append((
            buyer,
            po,
            style,
            color_string,
            val["total_qty"],
            val["com_qty"],
            val["bill_qty"]
        ))

    # 🔹 STATIC COLUMNS
    columns = [
        {"label": "Employee", "fieldname": "employee", "fieldtype": "Data", "width": 120},
        {"label": "Employee Name", "fieldname": "employee_name", "fieldtype": "Data", "width": 150},
    ]

    # 🔹 DYNAMIC COLUMNS
    for buyer, po, style, color_string, total_qty, com_qty, bill_qty in groups:

        scrubbed = frappe.scrub(f"{buyer}_{po}_{style}")

        header = f"{buyer} $ {po} | {style} | {color_string}${total_qty}${com_qty}${bill_qty}"

        columns += [
            {"label": f"{header} $ Name of Operation", "fieldname": f"{scrubbed}_operation", "fieldtype": "Small Text", "width": 140},
            {"label": f"{header} $ Bill Qty", "fieldname": f"{scrubbed}_bill", "fieldtype": "Small Text", "width": 90},
            {"label": f"{header} $ Bill Qty Dzn", "fieldname": f"{scrubbed}_bill_dzn", "fieldtype": "Small Text", "width": 90},
            {"label": f"{header} $ Rate Dzn", "fieldname": f"{scrubbed}_rate", "fieldtype": "Small Text", "width": 90},
            {"label": f"{header} $ Total", "fieldname": f"{scrubbed}_total", "fieldtype": "Small Text", "width": 110},

            {"label": f"{header} $ Bill Qty_num", "fieldname": f"{scrubbed}_bill_num", "fieldtype": "Currency", "width": 90},
            {"label": f"{header} $ Bill Qty Dzn_num", "fieldname": f"{scrubbed}_bill_dzn_num", "fieldtype": "Currency", "width": 90},
            {"label": f"{header} $ Total_num", "fieldname": f"{scrubbed}_total_num", "fieldtype": "Currency", "width": 110},
        ]

    return columns, groups


# ------------------------------------
# GET DATA
# ------------------------------------
def get_data(groups, filters):

    conditions, filters = get_conditions(filters)

    employees = frappe.db.sql(f"""
        SELECT DISTINCT dpd.employee, dpd.employee_name
        FROM `tabDaily Production Details` dpd
        JOIN `tabDaily Production` dp ON dpd.parent = dp.name
        WHERE {conditions}
        AND dpd.employee IS NOT NULL
        ORDER BY dpd.employee
    """, as_list=True)

    employees = [(e[0].strip(), (e[1] or "").strip()) for e in employees if e and e[0]]

    all_rows = frappe.db.sql(f"""
        SELECT 
            dpd.employee,
            dpd.employee_name,
            dpd.process_name,
            dp.buyer,
            dp.po,
            dp.style_list,
            dpd.quantity,
            dpd.quantity / 12 AS quantitydzn,
            dpd.rate,
            dpd.amount
        FROM `tabDaily Production` dp
        JOIN `tabDaily Production Details` dpd ON dp.name = dpd.parent
        WHERE {conditions}
    """, as_dict=True)

    # 🔹 GROUP DATA
    lookup = {}
    for r in all_rows:
        key = (r.employee, r.buyer, r.po, r.style_list)

        lookup.setdefault(key, []).append({
            "process_name": r.process_name,
            "quantity": r.quantity or 0,
            "quantitydzn": round(r.quantitydzn or 0, 2),
            "rate": r.rate or 0,
            "amount": round(r.amount or 0, 2),
        })

    data = []

    for emp, emp_name in employees:

        row = {
            "employee": emp,
            "employee_name": emp_name
        }

        for buyer, po, style, color_string, *_ in groups:

            key = (emp, buyer, po, style)
            processes = lookup.get(key, [])

            scrubbed = frappe.scrub(f"{buyer}_{po}_{style}")

            row[f"{scrubbed}_operation"] = "".join([
                f'<div class="line-cell">{p["process_name"]}</div>'
                for p in processes
            ])            
            
            row[f"{scrubbed}_bill"] = "".join([
                f'<div class="line-cell">{p["quantity"]}</div>'
                for p in processes
            ])

            row[f"{scrubbed}_bill_dzn"] = "".join([
                f'<div class="line-cell">{p["quantitydzn"]}</div>'
                for p in processes
            ])

            row[f"{scrubbed}_rate"] = "".join([
                f'<div class="line-cell">{p["rate"]}</div>'
                for p in processes
            ])

            row[f"{scrubbed}_total"] = "".join([
                f'<div class="line-cell">{p["amount"]}</div>'
                for p in processes
            ])

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