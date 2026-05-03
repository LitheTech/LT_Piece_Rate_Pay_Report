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
        _("Buyer") + ":Data:200",
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
        _("Total Bill") + ":Int:100",
        _("Salary") + ":Int:120",
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
                NULL, NULL, NULL,

                SUM(dp.bill_quantity) AS bill_qty_pcs,
                ROUND(SUM(dp.bill_quantity) / 12, 1) AS bill_qty_dzn,

                ROUND(
                    (SUM(dp.total_amount) / NULLIF(SUM(dp.bill_quantity), 0)) * 12,
                    1
                ) AS pcs_rate,

                SUM(dp.total_amount) AS bill,

                SUM(dpd_calc.stamp_deduct) AS stamp_deduct,

                SUM(dp.total_amount) - SUM(dpd_calc.stamp_deduct) AS total_bill,

                SUM(CASE 
                        WHEN emp.employment_type = 'salary' 
                        THEN dpd.amount 
                        ELSE 0 
                    END) AS salary

            FROM `tabDaily Production` dp

            LEFT JOIN `tabDaily Production Details` dpd
                ON dp.name = dpd.parent

            LEFT JOIN `tabEmployee` emp
                ON emp.name = dpd.employee

            -- 🔥 FIXED STAMP CALCULATION (NO invalid column)
            LEFT JOIN (
                SELECT
                    parent,
                    SUM(CASE WHEN amount > 1000 THEN 1 ELSE 0 END) * 10 AS stamp_deduct
                FROM `tabDaily Production Details`
                GROUP BY parent
            ) dpd_calc ON dp.name = dpd_calc.parent

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
				dp.buyer,
				dp.po,

				dpc.style,

				dp.bill_quantity,
				ROUND((dp.bill_quantity / 12), 1) AS bill_qty_dzn,
				ROUND((dp.total_amount * 12) / dp.bill_quantity, 1) AS pcs_rate,

				dp.total_amount,

				COUNT(CASE WHEN dpd.amount > 1000 THEN 1 END) * 10 AS stamp_deduct,

				dp.total_amount - (COUNT(CASE WHEN dpd.amount > 1000 THEN 1 END) * 10) AS total_bill,

				SUM(CASE 
						WHEN emp.employment_type = 'salary' 
						THEN dpd.amount 
						ELSE 0 
					END) AS salary

			FROM `tabDaily Production` dp

			JOIN `tabDaily Production Details` dpd
				ON dp.name = dpd.parent

			LEFT JOIN `tabEmployee` emp
				ON emp.name = dpd.employee

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
			)
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