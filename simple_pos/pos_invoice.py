import frappe
from frappe import _

def validate_invoice(doc, method):
    """Validate POS invoice"""
    if doc.is_pos:
        # Validate POS profile
        if doc.pos_profile:
            if not frappe.db.exists("POS Profile", doc.pos_profile):
                frappe.throw(_("POS Profile {0} does not exist").format(doc.pos_profile))
        
        # Validate items have stock
        for item in doc.items:
            if item.item_code:
                stock_qty = get_stock_qty(item.item_code, doc.pos_profile)
                if stock_qty < item.qty:
                    frappe.throw(_("Item {0} has insufficient stock. Available: {1}, Required: {2}").format(
                        item.item_code, stock_qty, item.qty
                    ))

def on_submit(doc, method):
    """Actions after POS invoice submission"""
    if doc.is_pos:
        # Update stock ledger
        update_stock_ledger(doc)
        # Create payment entries
        create_payment_entries(doc)

def on_cancel(doc, method):
    """Actions after POS invoice cancellation"""
    if doc.is_pos:
        # Reverse stock ledger
        reverse_stock_ledger(doc)
        # Cancel payment entries
        cancel_payment_entries(doc)

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

def update_stock_ledger(doc):
    """Update stock ledger for POS invoice"""
    # This will be handled by ERPNext's standard stock ledger updates
    pass

def reverse_stock_ledger(doc):
    """Reverse stock ledger for cancelled POS invoice"""
    # This will be handled by ERPNext's standard stock ledger reversals
    pass

def create_payment_entries(doc):
    """Create payment entries for POS invoice"""
    # This will be handled by ERPNext's standard payment entry creation
    pass

def cancel_payment_entries(doc):
    """Cancel payment entries for POS invoice"""
    # This will be handled by ERPNext's standard payment entry cancellation
    pass

def get_permission_query_conditions(user):
    """Get permission query conditions for POS invoices"""
    if user == "Administrator":
        return ""
    
    from frappe.desk.doctype.user.user import get_active_users
    user_roles = frappe.get_roles(user)
    
    if "POS Manager" in user_roles:
        return ""
    
    if "POS User" in user_roles:
        pos_profiles = frappe.get_all("POS Profile", 
            filters={"user": user},
            pluck="name"
        )
        if pos_profiles:
            return f"pos_profile IN ({', '.join([f"'{p}'" for p in pos_profiles])})"
    
    return "1=0"
