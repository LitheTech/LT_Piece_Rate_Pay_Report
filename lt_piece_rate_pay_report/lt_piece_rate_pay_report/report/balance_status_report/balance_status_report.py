# Copyright (c) 2026, LTL and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt


def execute(filters=None):
    if not filters:
        filters = {}

    columns = get_columns()
    data = get_data(filters)

    status = filters.get("remain_qty_status")
    
    if status == "Greater than Zero":
        # Equivalent to > 0
        data = [row for row in data if row["remain_qty"] > 0]
        
    elif status == "Zero or Less":
        # Equivalent to <= 0
        data = [row for row in data if row["remain_qty"] <= 0]

    return columns, data


def get_columns():
    return [
        _("Posting Date") + ":Date:120",
        _("Buyer") + ":Data:150",
        _("Master S/C") + ":Data:150",
        _("PO") + ":Data:150",
        _("Style") + ":Data:100",
        _("Color") + ":Data:100",
        _("Process Type") + ":Data:120",
        _("Total Qty") + ":Int:120",
        _("Completed Qty") + ":Int:120",
        _("Remain Qty") + ":Int:120",
    ]


def get_data(filters):

    master_processes = ["Cutting", "Sewing", "Iron"]

    prod_conditions, prod_params,po_query = get_conditions(filters)
    # -------------------------------------------------
    # PO DATA
    # -------------------------------------------------

    po_items = frappe.db.sql("""
        SELECT
            p.name AS po,
            p.posting_date AS po_date,
            p.buyer,
            p.sales_contract AS master_sc,
            c.style,
            c.color,
            c.quantity AS total_qty

        FROM `tabPO List` p

        LEFT JOIN `tabPO Details` c
            ON c.parent = p.name

        WHERE %s

    """%po_query, as_dict=1)

    # -------------------------------------------------
    # PRODUCTION DATA
    # -------------------------------------------------

    production_data = frappe.db.sql(f"""
        SELECT
            dp.po,
            dpc.style,
            dpc.color,
            dp.process_type,

            MAX(dp.production_date) AS latest_date,

            MAX(
                IFNULL(dpc.ongoing_quantity, 0)
                +
                IFNULL(dpc.done_quantity, 0)
            ) AS total_completed

        FROM `tabDaily Production` dp

        LEFT JOIN `tabDaily Production Colors` dpc
            ON dpc.parent = dp.name

        WHERE
            {prod_conditions}
            AND IFNULL(dp.is_revised, 0) != 1

        GROUP BY
            dp.po,
            dpc.style,
            dpc.color,
            dp.process_type

    """, prod_params, as_dict=1)

    # -------------------------------------------------
    # MAP
    # -------------------------------------------------

    prod_map = {
        (
            (p.po or "").strip(),
            (p.style or "").strip(),
            (p.color or "").strip(),
            (p.process_type or "").strip().lower(),
        ): p
        for p in production_data
    }

    # -------------------------------------------------
    # FINAL DATA
    # -------------------------------------------------

    data = []

    for item in po_items:
        if filters.get("style") and item.style != filters.get("style"): continue
        if filters.get("color") and item.color != filters.get("color"): continue


        for process in master_processes:

            if (
                filters.get("process_type")
                and process != filters.get("process_type")
            ):
                continue

            key = (
                (item.po or "").strip(),
                (item.style or "").strip(),
                (item.color or "").strip(),
                process.strip().lower(),
            )

            prod = prod_map.get(key)

            total_q = flt(item.total_qty)
            comp_q = flt(prod.total_completed) if prod else 0
            remain_q = total_q - comp_q

            data.append({
                "posting_date": item.po_date,
                "buyer": item.buyer,
                "master_s/c": item.master_sc,
                "po": item.po,
                "style": item.style,
                "color": item.color,
                "process_type": process,
                "total_qty": total_q,
                "completed_qty": comp_q,
                "remain_qty": remain_q if remain_q > 0 else 0,
            })

    return data


def get_conditions(filters):
    conditions = "1=1"
    params = {}
    po_query="1=1"
    if filters.get("buyer"):
        conditions += " AND dp.buyer = %(buyer)s"
        params["buyer"] = filters.get("buyer")
        po_query +=" AND p.buyer = '%s'" % filters["buyer"]
        
    if filters.get("company"):
        conditions += " AND dp.company = %(company)s"
        params["company"] = filters.get("company")
        po_query +=" AND p.company = '%s'" % filters["company"]

    if filters.get("sales_contract"):
        conditions += " AND dp.sales_contract = %(sc)s"
        params["sc"] = filters.get("sales_contract")
        po_query += " AND p.sales_contract = '%s'" % filters["sales_contract"]

    if filters.get("po_list"):
        conditions += " AND dp.po = %(po)s"
        params["po"] = filters.get("po_list")
        po_query += " AND p.name = '%s'" % filters["po_list"]

    if filters.get("style"):
        conditions += " AND dpc.style = %(style)s"
        params["style"] = filters.get("style")
        
    if filters.get("color"):
        conditions += " AND dpc.color = %(color)s"
        params["color"] = filters.get("color")

    if filters.get("from_date") and filters.get("to_date"):
        po_query+= " AND p.posting_date BETWEEN '%s' AND '%s'" % (
            filters["from_date"], filters["to_date"])
    
    return conditions, params, po_query

@frappe.whitelist()
def get_styles(po_list):

    return frappe.get_all(
        "PO Details",
        filters={"parent": po_list},
        pluck="style",
        distinct=True
    )


@frappe.whitelist()
def get_colors(po_list, style):

    return frappe.get_all(
        "PO Details",
        filters={
            "parent": po_list,
            "style": style
        },
        pluck="color",
        distinct=True
    )