import frappe
from frappe import _

@frappe.whitelist()
def get_items(pos_profile=None, item_group=None, search_term=None):
    """Get items for POS"""
    filters = {"disabled": 0, "is_sales_item": 1}
    if item_group:
        filters["item_group"] = item_group
    if search_term:
        filters["item_name"] = ["like", f"%{search_term}%"]

    items = frappe.get_all("Item",
        filters=filters,
        fields=["name", "item_name", "item_group", "standard_rate", "image", "stock_uom"],
        limit=100
    )
    return items

@frappe.whitelist()
def get_stock_qty(item_code, warehouse=None):
    """Get stock quantity for an item"""
    if not warehouse:
        return 0
    qty = frappe.db.get_value("Bin", {"item_code": item_code, "warehouse": warehouse}, "actual_qty")
    return qty or 0

@frappe.whitelist()
def create_invoice(customer, items, mode_of_payment=None, pos_profile=None):
    """Create a POS Sales Invoice"""
    import json
    if isinstance(items, str):
        items = json.loads(items)

    si = frappe.new_doc("Sales Invoice")
    si.is_pos = 1
    si.customer = customer
    if pos_profile:
        si.pos_profile = pos_profile

    for item in items:
        si.append("items", {
            "item_code": item.get("item_code"),
            "qty": item.get("qty", 1),
            "rate": item.get("rate", 0),
        })

    si.set_missing_values()
    si.save()

    if mode_of_payment:
        si.append("payments", {
            "mode_of_payment": mode_of_payment,
            "amount": si.grand_total,
        })

    si.submit()
    return si.name

@frappe.whitelist()
def get_customers(search_term=None):
    """Get customers for POS"""
    filters = {"disabled": 0}
    if search_term:
        filters["customer_name"] = ["like", f"%{search_term}%"]

    customers = frappe.get_all("Customer",
        filters=filters,
        fields=["name", "customer_name", "customer_group", "territory"],
        limit=100
    )
    return customers

@frappe.whitelist()
def get_pos_profiles():
    """Get available POS Profiles"""
    profiles = frappe.get_all("POS Profile",
        fields=["name", "company", "warehouse"],
        limit=50
    )
    return profiles
