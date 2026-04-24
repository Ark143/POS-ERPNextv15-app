import frappe
from frappe.model.document import Document

class POSProfile(Document):
    def validate(self):
        self.validate_warehouse()
        self.validate_payment_methods()
    
    def validate_warehouse(self):
        if self.warehouse:
            if not frappe.db.exists("Warehouse", self.warehouse):
                frappe.throw(f"Warehouse {self.warehouse} does not exist")
    
    def validate_payment_methods(self):
        if self.payment_methods:
            for method in self.payment_methods:
                if not frappe.db.exists("Mode of Payment", method.mode_of_payment):
                    frappe.throw(f"Mode of Payment {method.mode_of_payment} does not exist")
