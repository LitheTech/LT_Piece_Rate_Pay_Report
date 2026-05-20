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
                NULL, NULL, NULL, NULL, NULL,

                SUM(CASE WHEN dp.is_revised = 1 THEN 0 ELSE dp.bill_quantity END) AS bill_qty_pcs,
                ROUND(SUM(CASE WHEN dp.is_revised = 1 THEN 0 ELSE dp.bill_quantity END) / 12, 1) AS bill_qty_dzn,
                ROUND(
                    (SUM(dp.total_amount) / 
                    NULLIF(SUM(CASE WHEN dp.is_revised = 1 THEN 0 ELSE dp.bill_quantity END), 0)
                    ) * 12,
                    1
                ) AS pcs_rate,

                SUM(metrics.contract_amount) AS bill,
                IFNULL(SUM(stamp_metrics.stamp_deduct), 0) AS stamp_deduct,
                SUM(metrics.contract_amount) - IFNULL(SUM(stamp_metrics.stamp_deduct), 0) AS pc_bill,
                SUM(metrics.salary_amount) AS salary,
                SUM(dp.total_amount) - IFNULL(SUM(stamp_metrics.stamp_deduct), 0) AS total_bill

            FROM `tabDaily Production` dp

            LEFT JOIN (
                SELECT
                    parent,
                    SUM(CASE WHEN employee_type = 'contract' THEN amount ELSE 0 END) AS contract_amount,
                    SUM(CASE WHEN employee_type = 'salary' THEN amount ELSE 0 END) AS salary_amount
                FROM `tabDaily Production Details`
                GROUP BY parent
            ) metrics ON dp.name = metrics.parent

            -- Per-line stamp deduction logic (Total Mode)
            LEFT JOIN (
                SELECT 
                    first_dp.parent_name,
                    SUM(10) AS stamp_deduct
                FROM (
                    SELECT 
                        dpd.employee,
                        dp.facility_or_line,
                        MIN(dp.name) AS parent_name
                    FROM `tabDaily Production Details` dpd
                    JOIN `tabDaily Production` dp ON dpd.parent = dp.name
                    WHERE dpd.employee_type = 'contract'
                      AND %s
                    GROUP BY dpd.employee, dp.facility_or_line
                    HAVING SUM(dpd.amount) >= 1000 
                ) first_dp
                GROUP BY first_dp.parent_name
            ) stamp_metrics ON dp.name = stamp_metrics.parent_name

            WHERE
                %s

            GROUP BY dp.process_type
        """ % (conditions, conditions), as_list=1)

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

                IFNULL(metrics.contract_amount, 0) AS bill,
                IFNULL(stamp_metrics.stamp_deduct, 0) AS stamp_deduct,
                IFNULL(metrics.contract_amount, 0) - IFNULL(stamp_metrics.stamp_deduct, 0) AS pc_bill,
                IFNULL(metrics.salary_amount, 0) AS salary,
                dp.total_amount - IFNULL(stamp_metrics.stamp_deduct, 0) AS total_bill

            FROM `tabDaily Production` dp

            -- Fetch aggregated amounts safely
            LEFT JOIN (
                SELECT
                    parent,
                    SUM(CASE WHEN employee_type = 'contract' THEN amount ELSE 0 END) AS contract_amount,
                    SUM(CASE WHEN employee_type = 'salary' THEN amount ELSE 0 END) AS salary_amount
                FROM `tabDaily Production Details`
                GROUP BY parent
            ) metrics ON dp.name = metrics.parent

            -- Per-line stamp deduction logic (Detail Mode)
            LEFT JOIN (
                SELECT 
                    first_dp.parent_name,
                    SUM(10) AS stamp_deduct
                FROM (
                    SELECT 
                        dpd.employee, 
                        dp.facility_or_line,
                        MIN(dp.name) AS parent_name
                    FROM `tabDaily Production Details` dpd
                    JOIN `tabDaily Production` dp ON dpd.parent = dp.name
                    WHERE dpd.employee_type = 'contract'
                    AND %s
                    GROUP BY dpd.employee, dp.facility_or_line
                    HAVING SUM(dpd.amount) >= 1000
                ) first_dp
                GROUP BY first_dp.parent_name
            ) stamp_metrics ON dp.name = stamp_metrics.parent_name

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

        """ % (conditions, conditions), as_list=1)

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