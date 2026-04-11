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
        _("Process Type") + ":Data:200",

        # _("Total Qty") + ":Int:100",
        # _("Completed Qty") + ":Int:100",
		_("Bill") + ":Int:100",
		# _("Remain Qty") + ":Int:100",

        # _("Stamp Deduct") + ":Int:100",
		# _("Total Bill") + ":Int:100",

    ]

def get_data(filters):

	conditions, filters = get_conditions(filters)


	result = frappe.db.sql("""
 SELECT
    dp.process_type,
    sum(dp.total_amount)

    FROM `tabDaily Production` dp
    JOIN `tabDaily Production Colors` dpc 
        ON dpc.parent = dp.name
    WHERE %s
	group by dp.process_type

ORDER BY FIELD(dp.process_type, 'cutting', 'sewing', 'iron');


    """ % conditions, as_list=1)

	return result

def get_conditions(filters):
	conditions="1=1" 
	if filters.get("sales_contract"):conditions += " AND dp.sales_contract = '%s'" % filters["sales_contract"]
	if filters.get("po_list"):conditions += " AND dp.po = '%s'" % filters["po_list"]
	if filters.get("style_list"):conditions += " AND dp.style_list = '%s'" % filters["style_list"]
	if filters.get("color"):conditions += " AND dpc.color LIKE CONCAT('%%', {0}, '%%')".format(
        	frappe.db.escape(filters["color"])
    	)
	return conditions, filters



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
