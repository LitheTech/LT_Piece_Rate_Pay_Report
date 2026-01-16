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
        _("Production Date") + ":Data:90",
        _("Color") + ":Data:200",
        _("Process Type") + ":Data:200",
        # _("Style") + ":Data:90",
        # _("Sales Contract") + ":Data:200",
        _("Bill Qty (pcs)") + ":Int:100",
        _("Bill Qty(Dzn)") + ":Int:100",
		_("Pcs Rate") + ":Int:100",
		# _("Bill") + ":Int:100",

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
            dp.	total_quantity,
            dp.completed_quantity,
            dp.bill_quantity
            
        FROM `tabDaily Production` dp
        JOIN `tabDaily Production Details` dpd ON dp.name = dpd.parent
        WHERE %s
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