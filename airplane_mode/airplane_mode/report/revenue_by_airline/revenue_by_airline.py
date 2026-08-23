# Copyright (c) 2026, SymonMuchemi and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
    columns = get_columns()
    data = get_data()
    total_revenue = sum(row['revenue'] for row in data)
    summary = get_summary(total_revenue)
    chart = get_chart(data)

    return columns, data, None, chart, summary


def get_columns():
    return [
        {
            "label": _("Airline"),
            "fieldname": "airline",
            "fieldtype": "Link",
            "options": "Airline",
            "width": 200
        },
        {
            "label": _("Revenue"),
            "fieldname": "revenue",
            "fieldtype": "Currency",
            "width": 150
        }
    ]

def get_data():
    airlines_data = frappe.db.sql("""
        SELECT
            airline.name AS airline,
            COALESCE(SUM(ticket.total_amount), 0) AS revenue
        FROM
            `tabAirline` airline
        LEFT JOIN
            `tabAirplane` airplane ON airplane.airline = airline.name
        LEFT JOIN
            `tabAirplane Flight` flight ON flight.airplane = airplane.name
        LEFT JOIN
            `tabAirplane Ticket` ticket ON ticket.flight = flight.name
        GROUP BY
            airline.name
        ORDER BY
            revenue DESC
    """, as_dict=True)

    return airlines_data


def get_chart(data):
    labels = [row['airline'] for row in data]
    values = [row['revenue'] for row in data]

    chart = {
        "data": {
            "labels": labels,
            "datasets": [
                {
                    "name": _("Revenue"),
                    "values": values
                }
            ]
        },
        "type": "donut",
        "height": 250
    }

    return chart

def get_summary(total_revenue):
    return [
        {
            "label": _("Total Revenue"),
            "value": total_revenue,
            "indicator": "Green",
        }
    ]
