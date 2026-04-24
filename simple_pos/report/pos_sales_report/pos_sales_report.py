import frappe
from frappe import _

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {"label": _("Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 120},
        {"label": _("Invoice"), "fieldname": "name", "fieldtype": "Link", "options": "Sales Invoice", "width": 150},
        {"label": _("Customer"), "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 200},
        {"label": _("Item"), "fieldname": "item_name", "fieldtype": "Data", "width": 200},
        {"label": _("Quantity"), "fieldname": "qty", "fieldtype": "Float", "width": 100},
        {"label": _("Rate"), "fieldname": "rate", "fieldtype": "Currency", "width": 100},
        {"label": _("Amount"), "fieldname": "amount", "fieldtype": "Currency", "width": 120},
        {"label": _("Payment Method"), "fieldname": "mode_of_payment", "fieldtype": "Data", "width": 150},
    ]

def get_data(filters):
    conditions = get_conditions(filters)
    
    query = """
        SELECT 
            si.posting_date,
            si.name,
            si.customer,
            sii.item_code,
            sii.item_name,
            sii.qty,
            sii.rate,
            sii.amount,
            sip.mode_of_payment
        FROM 	abSales Invoice si
        INNER JOIN 	abSales Invoice Item sii ON si.name = sii.parent
        LEFT JOIN 	abSales Invoice Payment sip ON si.name = sip.parent
        WHERE si.is_pos = 1
        AND si.docstatus = 1
        {conditions}
        ORDER BY si.posting_date DESC, si.creation DESC
    """.format(conditions=conditions)
    
    data = frappe.db.sql(query, as_dict=1)
    return data

def get_conditions(filters):
    conditions = ""
    
    if filters.get("from_date"):
        conditions += " AND si.posting_date >= '{}'".format(filters["from_date"])
    
    if filters.get("to_date"):
        conditions += " AND si.posting_date <= '{}'".format(filters["to_date"])
    
    if filters.get("customer"):
        conditions += " AND si.customer = '{}'".format(filters["customer"])
    
    if filters.get("pos_profile"):
        conditions += " AND si.pos_profile = '{}'".format(filters["pos_profile"])
    
    return conditions
