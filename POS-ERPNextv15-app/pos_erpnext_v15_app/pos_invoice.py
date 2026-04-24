import frappe
from frappe import _

def validate_invoice(doc, method):
    """Validate POS invoice"""
    if doc.is_pos:
        if doc.pos_profile:
            if not frappe.db.exists("POS Profile", doc.pos_profile):
                frappe.throw(_("POS Profile {0} does not exist").format(doc.pos_profile))

def on_submit(doc, method):
    """Actions after POS invoice submission"""
    pass

def on_cancel(doc, method):
    """Actions after POS invoice cancellation"""
    pass
