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
        _("Production Date") + ":Data:130",
        _("Color") + ":Data:150",
        _("Process Type") + ":Data:100",
		_("Floor") + ":Data:70",
		_("Line") + ":Data:50",
        # _("Style") + ":Data:90",
        # _("Sales Contract") + ":Data:200",
        _("Total Qty") + ":Int:100",
        _("Completed Qty") + ":Int:100",
		_("Bill Qty") + ":Int:100",
		_("Remain Qty") + ":Int:100",

        # _("Stamp Deduct") + ":Int:100",
		# _("Total Bill") + ":Int:100",

    ]

def get_data(filters):

	conditions, filters = get_conditions(filters)


	result = frappe.db.sql("""
        SELECT 
            dp.production_date,
            dp.color,
            dp.process_type,
			dp.floor,
			dp.facility_or_line,
            dp.total_quantity,
            dp.completed_quantity,
            dp.bill_quantity,
			dp.total_quantity-dp.completed_quantity-dp.bill_quantity
            
        FROM `tabDaily Production` dp
        WHERE %s
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
	if filters.get("process_type"):conditions += " AND dp.process_type = '%s'" % filters["process_type"]
	if filters.get("floor"):conditions += " AND dp.floor = '%s'" % filters["floor"]
	if filters.get("line"):conditions += " AND dp.facility_or_line = '%s'" % filters["line"]
	if filters.get("company"): conditions += " AND dp.company = '%s'" % filters["company"]
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
