import frappe
from frappe import _
from frappe.model.document import Document

class POSProfile(Document):
    def validate(self):
        if not self.warehouse:
            frappe.throw(_("Warehouse is required"))
        if not self.payments:
            frappe.throw(_("At least one payment method is required"))
