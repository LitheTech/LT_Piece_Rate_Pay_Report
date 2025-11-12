import frappe

def execute(filters=None):
    if not filters:
        filters = {}

    columns, buyers = get_columns(filters)
    data = get_data(buyers,filters)
    return columns, data


def get_columns(filters):

    conditions, filters = get_conditions(filters)

    # Fetch distinct combinations of buyer, po, style_list, color
    rows = frappe.db.sql("""
        SELECT DISTINCT dp.buyer, dp.po, dp.style_list, dp.color,dp.total_quantity,dp.completed_quantity,dp.bill_quantity
        FROM `tabDaily Production` dp
        WHERE buyer IS NOT NULL AND buyer != ''
          AND po IS NOT NULL AND po != ''
          AND style_list IS NOT NULL AND style_list != ''
          AND color IS NOT NULL AND color != '' and %s
    """ % conditions,as_list=True)

    # Normalize into list of tuples
    buyers = []
    for r in rows:
        if not r or len(r) < 7:
            continue
        buyer, po, style, color,total_qty,com_qty,bill_qty = map(lambda x: str(x or "").strip(), r)
        buyers.append((buyer, po, style, color,total_qty,com_qty,bill_qty))

    # Flat columns for Frappe report
    flat_columns = [
        {"label": "Employee", "fieldname": "employee", "fieldtype": "Data", "width": 150},
        {"label": "Employee Name", "fieldname": "employee_name", "fieldtype": "Data", "width": 150},
    ]

    for buyer, po, style, color,total_qty,com_qty,bill_qty in buyers:
        key = f"{buyer}_{po}_{style}_{color}"
        scrubbed = frappe.scrub(key)
        flat_columns += [
            {"label": f"{buyer} ${po} | {style} | {color}${total_qty}${com_qty}${bill_qty} $ Bill Qty", "fieldname": f"{scrubbed}_bill", "fieldtype": "Int", "width": 80},
            {"label": f"{buyer} ${po} | {style} | {color}${total_qty}${com_qty}${bill_qty} $ Bill Qty Dzn", "fieldname": f"{scrubbed}_bill_dzn", "fieldtype": "Float","precision": 2, "width": 80},
            {"label": f"{buyer} ${po} | {style} | {color}${total_qty}${com_qty}${bill_qty} $ Rate Dzn", "fieldname": f"{scrubbed}_rate", "fieldtype": "Float","precision": 1, "width": 80},
            {"label": f"{buyer} ${po} | {style} | {color}${total_qty}${com_qty}${bill_qty} $ Total", "fieldname": f"{scrubbed}_total", "fieldtype": "Int", "width": 100},
        ]

    # Header rows for JS/HTML formatter (optional)
    # header_row_1 = ["Employee"]
    # header_row_2 = [""]

    # for buyer, po, style, color in buyers:
    #     header_row_1 += [f"{buyer}\nPO: {po}\nStyle: {style}\nColor: {color}", "", ""]
    #     header_row_2 += ["Bill", "Rate", "Total"]

    return flat_columns, buyers


def get_data(buyers, filters):
    conditions, filters = get_conditions(filters)

    employees = frappe.db.sql("""
        SELECT DISTINCT dpd.employee, dpd.employee_name
        FROM `tabDaily Production Details` dpd
        JOIN `tabDaily Production` dp ON dpd.parent = dp.name
        where %s
        AND dpd.employee IS NOT NULL AND dpd.employee != ''
    """%conditions, as_list=True)
    employees = [(e[0].strip(), e[1].strip() if e[1] else "") for e in employees if e and e[0]]

    all_rows = frappe.db.sql("""
        SELECT 
            dpd.employee,
            dpd.employee_name,
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
        where %s
    """%conditions, as_dict=True)

    lookup = {}
    for r in all_rows:
        key = (
            str(r.get("employee") or "").strip(),
            str(r.get("buyer") or "").strip(),
            str(r.get("po") or "").strip(),
            str(r.get("style_list") or "").strip(),
            str(r.get("color") or "").strip()
        )

        existing = lookup.get(key, {"quantity": 0, "quantitydzn": 0, "rate": 0, "amount": 0})
        existing["quantity"] += r.get("quantity") or 0
        existing["quantitydzn"] += r.get("quantitydzn") or 0
        existing["rate"] = r.get("rate") or existing.get("rate") or 0
        existing["amount"] += r.get("amount") or (existing["quantity"] * existing["rate"])
        lookup[key] = existing

    data = []
    for emp, emp_name in employees:
        row = {"employee": emp, "employee_name": emp_name or frappe.db.get_value("Employee", emp, "employee_name") or ""}
        for buyer, po, s, color,total_qty,com_qty,bill_qty in buyers:
            key = (str(emp).strip(), str(buyer).strip(), str(po).strip(), str(s).strip(), str(color).strip())
            rec = lookup.get(key, {"quantity": 0, "quantitydzn": 0, "rate": 0, "amount": 0})
            qty = rec.get("quantity") or 0
            qtydzn = rec.get("quantitydzn") or 0
            rate = rec.get("rate") or 0
            total = rec.get("amount") or (qtydzn * rate)

            scrubbed = frappe.scrub(f"{buyer}_{po}_{s}_{color}")
            row[f"{scrubbed}_bill"] = qty
            row[f"{scrubbed}_bill_dzn"] = qtydzn
            row[f"{scrubbed}_rate"] = rate
            row[f"{scrubbed}_total"] = total

        data.append(row)

    return data


def get_conditions(filters):
    conditions = ""  # always true, helps in easy concatenation

    if filters.get("start_date") and filters.get("end_date"):
        conditions += " dp.production_date BETWEEN '%s' AND '%s'" % (
            filters["start_date"],
            filters["end_date"],
        )

    if filters.get("floor"):
        conditions += " AND dp.floor = '%s'" % filters["floor"]

    if filters.get("line"):
        conditions += " AND dp.facility_or_line = '%s'" % filters["line"]

    if filters.get("buyer"):
        conditions += " AND dp.buyer = '%s'" % filters["buyer"]

    if filters.get("process_type"):
        conditions += " AND dp.process_type = '%s'" % filters["process_type"]

    return conditions, filters