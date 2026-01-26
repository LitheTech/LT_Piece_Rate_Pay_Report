# Copyright (c) 2025, Lithe-Tech LTD and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):

	if not filters:
		filters = {}

	columns = get_columns()
	data = get_data(filters)
	
	return columns, data

def get_columns():
	return [
        # _("Production Date") + ":Data:90",
        # _("Color") + ":Data:200",
        _("Process Type") + ":Data:200",
        # _("Style") + ":Data:90",
        # _("Sales Contract") + ":Data:200",
        _("Total Qty") + ":Int:100",
        _("Completed Qty") + ":Int:100",
		# _("Bill Qty") + ":Int:100",
		_("Remain Qty") + ":Int:100",

        # _("Stamp Deduct") + ":Int:100",
		# _("Total Bill") + ":Int:100",

    ]

def get_data(filters):

	conditions, filters = get_conditions(filters)


	result = frappe.db.sql("""
 SELECT
    process_type,
    total_quantity,
    completed_qty,
    remaining_qty
FROM (
    SELECT
        dp.process_type,
        dp.total_quantity,
        dp.completed_quantity + dp.bill_quantity AS completed_qty,
        dp.total_quantity - dp.completed_quantity - dp.bill_quantity AS remaining_qty,
        ROW_NUMBER() OVER (
            PARTITION BY dp.process_type
            ORDER BY (dp.completed_quantity + dp.bill_quantity) DESC
        ) AS rn
    FROM `tabDaily Production` dp
    WHERE %s
) x
WHERE rn = 1
ORDER BY FIELD(process_type, 'cutting', 'sewing', 'iron');


    """ % conditions, as_list=1)

	return result

def get_conditions(filters):
	conditions="1=1" 
	if filters.get("po_list"):conditions += " AND dp.po = '%s'" % filters["po_list"]
	if filters.get("style_list"):conditions += " AND dp.style_list = '%s'" % filters["style_list"]
	if filters.get("color"):conditions += " AND dp.color LIKE CONCAT('%%', {0}, '%%')".format(
        	frappe.db.escape(filters["color"])
    	)
	return conditions, filters


import frappe

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
