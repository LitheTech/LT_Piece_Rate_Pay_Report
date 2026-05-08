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
        _("Process Type") + ":Data:90",
		_("Line") + ":Data:90",
        _("Buyer") + ":Data:200",
		_("Sales Contract") + ":Data:90",
        _("Po") + ":Data:200",
        _("Style") + ":Data:90",

        _("Bill Qty (pcs)") + ":Int:100",
        {
            "label": "Bill Qty(Dzn)",
            "fieldname": "bill_qty_dzn",
            "fieldtype": "Float",
            "precision": 1,
            "width": 100
        },
        {
            "label": "Pcs Rate",
            "fieldname": "pcs_rate",
            "fieldtype": "Float",
            "precision": 1,
            "width": 100
        },

        _("Bill") + ":Int:100",
        _("Stamp Deduct") + ":Int:100",
        _("PC Bill") + ":Int:100",
        _("Salary") + ":Int:120",
		_("Total Bill") + ":Int:100",
    ]


def get_data(filters):

	conditions, filters = get_conditions(filters)

	# =========================
	# SHOW TOTAL MODE
	# =========================
	if filters.get("show_total"):

		result = frappe.db.sql("""
            SELECT
                dp.process_type,
                NULL, NULL, NULL,NULL,NULL,

				SUM(CASE WHEN dp.is_revised = 1 THEN 0 ELSE dp.bill_quantity END) AS bill_qty_pcs,

				-- Total Quantity in Dozen
				ROUND(SUM(CASE WHEN dp.is_revised = 1 THEN 0 ELSE dp.bill_quantity END) / 12, 1) AS bill_qty_dzn,

				-- Rate calculation (Handling NULLIF to prevent division by zero)
				ROUND(
					(SUM(dp.total_amount) / 
					NULLIF(SUM(CASE WHEN dp.is_revised = 1 THEN 0 ELSE dp.bill_quantity END), 0)
					) * 12,
					1
				) AS pcs_rate,

				SUM(metrics.contract_amount) AS bill,
					SUM(metrics.stamp_deduct) AS stamp_deduct,
					SUM(metrics.contract_amount) - SUM(metrics.stamp_deduct) AS pc_bill,
					SUM(metrics.salary_amount) AS salary,
					
					-- Final Total: Main Total Amount minus the Stamp Deductions
					SUM(dp.total_amount) - SUM(metrics.stamp_deduct) AS total_bill

				FROM `tabDaily Production` dp

				LEFT JOIN (
					SELECT
						parent,
						-- Total amount for contract employees only
						SUM(CASE WHEN employee_type = 'contract' THEN amount ELSE 0 END) AS contract_amount,
						
						-- Total amount for salary employees only
						SUM(CASE WHEN employee_type = 'salary' THEN amount ELSE 0 END) AS salary_amount,
						
						-- Stamp logic: count contract rows > 1000 and multiply by 10
						SUM(CASE WHEN amount > 1000 AND employee_type = 'contract' THEN 10 ELSE 0 END) AS stamp_deduct
					FROM `tabDaily Production Details`
					GROUP BY parent
				) metrics ON dp.name = metrics.parent
			WHERE
				%s

			GROUP BY dp.process_type
        """ % conditions, as_list=1)

	# =========================
	# DETAIL MODE
	# =========================
	else:

		result = frappe.db.sql("""
			SELECT
				dp.process_type,
				dp.facility_or_line,
				dp.buyer,
				dp.sales_contract,
				dp.po,

				dpc.style,

				CASE WHEN dp.is_revised = 1 THEN 0 ELSE dp.bill_quantity END AS bill_quantity,
        		ROUND((CASE WHEN dp.is_revised = 1 THEN 0 ELSE dp.bill_quantity END / 12), 1) AS bill_qty_dzn,
				CASE 
					WHEN dp.is_revised = 1 OR dp.bill_quantity = 0 THEN 0 
					ELSE ROUND((dp.total_amount * 12) / dp.bill_quantity, 1) 
				END AS pcs_rate,

				SUM(CASE 
						WHEN dpd.employee_type = 'contract' 
						THEN dpd.amount 
						ELSE 0 
					END) AS bill,

				COUNT(CASE WHEN dpd.amount > 1000 AND dpd.employee_type = 'contract' THEN 1 END) * 10 AS stamp_deduct,
				
				SUM(CASE WHEN dpd.employee_type = 'contract' THEN dpd.amount ELSE 0 END) -(COUNT(CASE WHEN dpd.amount > 1000 AND dpd.employee_type = 'contract' THEN 1 END) * 10) AS pc_bill,


				SUM(CASE 
						WHEN dpd.employee_type = 'salary' 
						THEN dpd.amount 
						ELSE 0 
					END) AS salary,
				
				dp.total_amount - (COUNT(CASE WHEN dpd.amount > 1000 AND dpd.employee_type = 'contract' THEN 1 END) * 10) AS total_bill

			FROM `tabDaily Production` dp

			JOIN `tabDaily Production Details` dpd
				ON dp.name = dpd.parent


			LEFT JOIN (
				SELECT
					parent,
					GROUP_CONCAT(
						CONCAT(style, '-', color, '=', ongoing_quantity)
						SEPARATOR ', '
					) AS style
				FROM `tabDaily Production Colors`
				GROUP BY parent
			) dpc ON dpc.parent = dp.name

			WHERE
				%s

			GROUP BY dp.name

			ORDER BY FIELD(
				dp.process_type,
				'cutting',
				'sewing',
				'iron'
			),
			dp.facility_or_line ASC

		""" % conditions, as_list=1)

	return result


def get_conditions(filters):
	conditions = "1=1"

	if filters.get("start_date") and filters.get("end_date"):
		conditions += " AND dp.production_date BETWEEN '%s' AND '%s'" % (
			filters["start_date"],
			filters["end_date"]
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