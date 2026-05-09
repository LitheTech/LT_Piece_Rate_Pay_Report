# Copyright (c) 2025, Lithe-Tech LTD and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, money_in_words



def execute(filters=None):

	if not filters:
		filters = {}

	columns = get_columns()
	data = get_data(filters)
	
	return columns, data

def get_columns():
	return [
        _("Process Type") + ":Data:200",

        _("Po") + ":Data:200",
        _("Style") + ":Data:90",
        _("Color") + ":Data:90",

        ("Quantity") + ":Int:100",
		_("Bill Amount") + ":Int:100",

    ]

def get_data(filters):
    if not filters.get("sales_contract"):
        return []

    master_processes = ["Cutting", "Sewing", "Iron"]

    # 1. Get Styles and Colors from the PO List
    po_items = frappe.db.sql("""
        SELECT 
            parent.name as po,
            child.style, 
            child.color
        FROM `tabPO List` parent
        JOIN `tabPO Details` child ON child.parent = parent.name
        WHERE parent.sales_contract = %(sc)s
    """, {"sc": filters.get("sales_contract")}, as_dict=1)

    # 2. SQL: Calculate the value for EACH DP record first, then sum them up
    prod_conditions, params = get_conditions(filters)
    
    production_data = frappe.db.sql(f"""
        SELECT 
            sub.po,
            sub.style, 
            sub.color, 
            sub.process_type,
            SUM(sub.calc_amount) as total_bill_amount,
            SUM(sub.ongoing_qty) as total_ongoing_qty
        FROM (
            SELECT 
                dp.po,
                dpc.style, 
                dpc.color, 
                dp.process_type,
                dpc.ongoing_quantity as ongoing_qty,
                /* Calculation per DP record: (Total Amt / Bill Qty) * Ongoing Qty */
                CASE 
                    WHEN IFNULL(dp.bill_quantity, 0) > 0 
                    THEN (dp.total_amount / dp.bill_quantity) * dpc.ongoing_quantity 
                    ELSE 0 
                END as calc_amount
            FROM `tabDaily Production` dp
            JOIN `tabDaily Production Colors` dpc ON dpc.parent = dp.name
            WHERE {prod_conditions}
        ) AS sub
        GROUP BY sub.po, sub.style, sub.color, sub.process_type
    """, params, as_dict=1)

    # 3. Map the aggregated results
    prod_map = {
        (p.po, p.style, p.color, p.process_type.strip().title()): {
            "quantity": p.total_ongoing_qty or 0,
            "bill_amount": p.total_bill_amount or 0
        } 
        for p in production_data
    }

    data = []

    # 4. Build the final row list
    for item in po_items:
        if filters.get("po_list") and item.po != filters.get("po_list"):
            continue
        if filters.get("style") and item.style != filters.get("style"):
            continue
        if filters.get("color") and item.color != filters.get("color"):
            continue

        for process in master_processes:
            if filters.get("process_type") and process != filters.get("process_type"):
                continue

            key = (item.po, item.style, item.color, process)
            prod_values = prod_map.get(key, {"quantity": 0, "bill_amount": 0})

            data.append({
                "process_type": process,
                "po": item.po,
                "style": item.style,
                "color": item.color,
                "quantity": prod_values["quantity"],
                "bill_amount": flt(prod_values["bill_amount"], 2) # Ensure 2 decimal places
            })

    return data


def get_conditions(filters):
    conditions = "1=1"
    params = {}

    if filters.get("sales_contract"):
        conditions += " AND dp.sales_contract = %(sales_contract)s"
        params["sales_contract"] = filters.get("sales_contract")

    if filters.get("po_list"):
        conditions += " AND dp.po = %(po_list)s"
        params["po_list"] = filters.get("po_list")

    if filters.get("style"):
        conditions += " AND dpc.style = %(style)s"
        params["style"] = filters.get("style")

    if filters.get("color"):
        conditions += " AND dpc.color = %(color)s"
        params["color"] = filters.get("color")
        
    if filters.get("process_type"):
        conditions += " AND dp.process_type = %(process_type)s"
        params["process_type"] = filters.get("process_type")

    return conditions, params



@frappe.whitelist()
def get_styles(po_list):
    po = frappe.get_doc("PO List", po_list)

    styles = set()
    for row in po.po_details:
        if row.style:
            styles.add(row.style)

    return list(styles)


@frappe.whitelist()
def get_colors(po_list, style):
    po = frappe.get_doc("PO List", po_list)

    colors = set()
    for row in po.po_details:
        if row.style == style and row.color:
            colors.add(row.color)

    return list(colors)
