import frappe
from frappe import _

def before_install():
    """Actions before app installation"""
    pass

def after_install():
    """Actions after app installation"""
    # Create default roles
    create_pos_roles()

def create_pos_roles():
    """Create POS User and POS Manager roles"""
    for role_name in ["POS User", "POS Manager"]:
        if not frappe.db.exists("Role", role_name):
            role = frappe.get_doc({
                "doctype": "Role",
                "role_name": role_name,
                "desk_access": 1 if role_name == "POS Manager" else 0,
            })
            role.insert(ignore_permissions=True)
