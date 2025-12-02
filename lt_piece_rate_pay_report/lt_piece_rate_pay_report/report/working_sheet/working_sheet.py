import frappe

def execute(filters=None):
    if not filters:
        filters = {}

    columns, buyers = get_columns(filters)
    data = get_data(buyers, filters)
    return columns, data


# ------------------------------------
# GET COLUMNS
# ------------------------------------
def get_columns(filters):

    conditions, filters = get_conditions(filters)

    rows = frappe.db.sql("""
        SELECT DISTINCT dp.buyer, dp.po, dp.style_list, dp.color,
                        dp.total_quantity, dp.completed_quantity, dp.bill_quantity
        FROM `tabDaily Production` dp
        WHERE buyer IS NOT NULL AND buyer != ''
          AND po IS NOT NULL AND po != ''
          AND style_list IS NOT NULL AND style_list != ''
          AND color IS NOT NULL AND color != '' 
          AND %s
        ORDER BY buyer
    """ % conditions, as_list=True)

    buyers = []
    for r in rows:
        if not r or len(r) < 7:
            continue

        buyer, po, style, color, total_qty, com_qty, bill_qty = map(lambda x: str(x or "").strip(), r)
        buyers.append((buyer, po, style, color, total_qty, com_qty, bill_qty))

    # Basic columns
    flat_columns = [
        {"label": "Employee", "fieldname": "employee", "fieldtype": "Data", "width": 120},
        {"label": "Employee Name", "fieldname": "employee_name", "fieldtype": "Data", "width": 150},
    ]

    # Dynamic columns for each buyer+po+style+color
    for buyer, po, style, color, total_qty, com_qty, bill_qty in buyers:

        key = f"{buyer}_{po}_{style}_{color}"
        scrubbed = frappe.scrub(key)
        header = f"{buyer} ${po} | {style} | {color}${total_qty}${com_qty}${bill_qty}"

        flat_columns += [
            {"label": f"{header} $ Name of Operation", "fieldname": f"{scrubbed}_operation", "fieldtype": "Small Text", "width": 140},
            {"label": f"{header} $ Rate Dzn", "fieldname": f"{scrubbed}_rate", "fieldtype": "Small Text", "width": 90},
            {"label": f"{header} $ Bill Qty", "fieldname": f"{scrubbed}_bill", "fieldtype": "Small Text", "width": 90},
            {"label": f"{header} $ Bill Qty Dzn", "fieldname": f"{scrubbed}_bill_dzn", "fieldtype": "Small Text", "width": 90},

            # FIXED: MULTILINE RATES NEED SMALL TEXT
            

            {"label": f"{header} $ Total", "fieldname": f"{scrubbed}_total", "fieldtype": "Small Text", "width": 110},

            {"label": f"{header} $ Bill Qty_num", "fieldname": f"{scrubbed}_bill_num", "fieldtype": "Float","precision": 1, "width": 90}, # num=number(float/int)
            {"label": f"{header} $ Bill Qty Dzn_num", "fieldname": f"{scrubbed}_bill_dzn_num", "fieldtype": "Float","precision": 1, "width": 90},
            {"label": f"{header} $ Total_num", "fieldname": f"{scrubbed}_total_num", "fieldtype": "Float","precision": 1, "width": 110},

        ]

    return flat_columns, buyers


# ------------------------------------
# GET DATA
# ------------------------------------
def get_data(buyers, filters):

    conditions, filters = get_conditions(filters)

    # List of employees
    employees = frappe.db.sql("""
        SELECT DISTINCT dpd.employee, dpd.employee_name
        FROM `tabDaily Production Details` dpd
        JOIN `tabDaily Production` dp ON dpd.parent = dp.name
        WHERE %s
        AND dpd.employee IS NOT NULL AND dpd.employee != ''
        order by dpd.employee
    """ % conditions, as_list=True)

    employees = [(e[0].strip(), (e[1] or "").strip()) for e in employees if e and e[0]]

    # Fetch detailed rows
    all_rows = frappe.db.sql("""
        SELECT 
            dpd.employee,
            dpd.employee_name,
            dpd.process_name,
            dp.buyer,
            dp.po,
            dp.style_list,
            dp.color,
            dpd.quantity,
            dpd.quantity / 12 AS quantitydzn,
            dpd.rate,
            dpd.amount
        FROM `tabDaily Production` dp
        JOIN `tabDaily Production Details` dpd ON dp.name = dpd.parent
        WHERE %s
        GROUP BY dpd.employee, dp.buyer, dp.po, dp.style_list, dp.color, dpd.process_name
    """ % conditions, as_dict=True)

    # Build lookup table
    lookup = {}
    for r in all_rows:
        key = (
            (r.get("employee") or "").strip(),
            (r.get("buyer") or "").strip(),
            (r.get("po") or "").strip(),
            (r.get("style_list") or "").strip(),
            (r.get("color") or "").strip(),
        )
        lookup.setdefault(key, []).append({
            "process_name": r.get("process_name") or "",
            "quantity": r.get("quantity") or "",
            "quantitydzn": round(r.get("quantitydzn") or 0, 1),
            "rate": r.get("rate") or 0,
            "amount": round(r.get("amount") or 0, 1),
        })

    data = []

    # ------------------------------------
    # BUILD EMPLOYEE ROWS
    # ------------------------------------
    for emp, emp_name in employees:

        row = {
            "employee": emp,
            "employee_name": emp_name
        }

        for buyer, po, s, color, total_qty, com_qty, bill_qty in buyers:

            key = (emp, buyer, po, s, color)
            processes = lookup.get(key, [])
            scrubbed = frappe.scrub(f"{buyer}_{po}_{s}_{color}")

            # MULTILINE TEXT FIELDS
            process_names = "\n".join([p["process_name"] for p in processes]) or ""
            rate_lines = "\n".join([str(p["rate"]) for p in processes]) or ""

            # Total numeric values
            bill_qty_total = "\n".join([str(p["quantity"]) for p in processes]) or ""
            bill_dzn_total = "\n".join([str(p["quantitydzn"]) for p in processes])
            total_amount = "\n".join([str(p["amount"]) for p in processes])

            bill_qty_total_num = sum([p["quantity"] for p in processes])
            bill_dzn_total_num = sum([p["quantitydzn"] for p in processes])
            total_amount_num = sum([p["amount"] for p in processes])

            # Fill row
            row[f"{scrubbed}_operation"] = process_names
            row[f"{scrubbed}_bill"] = bill_qty_total
            row[f"{scrubbed}_bill_dzn"] = bill_dzn_total
            row[f"{scrubbed}_rate"] = rate_lines      # FIXED
            row[f"{scrubbed}_total"] = total_amount
            row[f"{scrubbed}_bill_num"] = bill_qty_total_num
            row[f"{scrubbed}_bill_dzn_num"] = bill_dzn_total_num
            row[f"{scrubbed}_total_num"] = total_amount_num

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

    # if filters.get("process"):
        # conditions += " AND dpd.process= '%s'" % filters["process"]

    return conditions, filters