import frappe

def before_install():
    """Run before app installation"""
    pass

def after_install():
    """Run after app installation"""
    # Create default roles
    create_roles()
    # Create default POS settings
    create_pos_settings()

def create_roles():
    """Create POS-specific roles"""
    if not frappe.db.exists("Role", "POS User"):
        frappe.get_doc({
            "doctype": "Role",
            "role_name": "POS User",
            "desk_access": 1,
            "is_standard": 1
        }).insert()
    
    if not frappe.db.exists("Role", "POS Manager"):
        frappe.get_doc({
            "doctype": "Role",
            "role_name": "POS Manager",
            "desk_access": 1,
            "is_standard": 1
        }).insert()

def create_pos_settings():
    """Create default POS settings"""
    if not frappe.db.exists("DocType", "POS Settings"):
        frappe.get_doc({
            "doctype": "DocType",
            "module": "Simple POS",
            "name": "POS Settings",
            "custom": 0,
            "is_single": 1
        }).insert()
