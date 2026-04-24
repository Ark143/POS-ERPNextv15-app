import frappe
from frappe import _

@frappe.whitelist()
def get_items(pos_profile=None, item_group=None, search_text=None):
    """Get available items for POS"""
    filters = {"is_sales_item": 1, "disabled": 0}
    
    if item_group:
        filters["item_group"] = item_group
    
    if search_text:
        filters["item_name"] = ["like", f"%{search_text}%"]
    
    items = frappe.get_all("Item", 
        filters=filters,
        fields=["name", "item_code", "item_name", "item_group", "stock_uom", "image"],
        limit=100
    )
    
    # Get stock quantities
    for item in items:
        item["stock_qty"] = get_stock_qty(item["name"], pos_profile)
    
    return items

@frappe.whitelist()
def get_stock_qty(item_code, pos_profile):
    """Get available stock quantity for an item"""
    if not pos_profile:
        return 0
    
    pos_profile_doc = frappe.get_doc("POS Profile", pos_profile)
    warehouse = pos_profile_doc.warehouse
    
    bin_data = frappe.db.get_value("Bin", 
        {"item_code": item_code, "warehouse": warehouse},
        "actual_qty"
    )
    
    return bin_data or 0

@frappe.whitelist()
def create_invoice(data):
    """Create a POS invoice"""
    import json
    
    if isinstance(data, str):
        data = json.loads(data)
    
    invoice = frappe.new_doc("Sales Invoice")
    invoice.update(data)
    invoice.is_pos = 1
    invoice.pos_profile = data.get("pos_profile")
    
    invoice.insert()
    invoice.submit()
    
    return invoice.name

@frappe.whitelist()
def get_customers():
    """Get list of customers"""
    customers = frappe.get_all("Customer",
        fields=["name", "customer_name", "customer_group"],
        limit=100
    )
    return customers

@frappe.whitelist()
def get_pos_profiles():
    """Get POS profiles for current user"""
    profiles = frappe.get_all("POS Profile",
        filters={"user": frappe.session.user},
        fields=["name", "pos_profile_name", "warehouse", "company"]
    )
    return profiles
