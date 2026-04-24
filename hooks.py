# App Hooks
app_name = "simple_pos"
app_title = "Simple POS"
app_publisher = "Ark143"
app_description = "Simple Point of Sale Application for ERPNext v15"
app_icon = "octicon octicon-device-desktop"
app_color = "#3498db"
app_email = "support@example.com"
app_license = "MIT"

# Installation
before_install = "simple_pos.install.before_install"
after_install = "simple_pos.install.after_install"

# DocType Events
doc_events = {
    "Sales Invoice": {
        "validate": "simple_pos.pos_invoice.validate_invoice",
        "on_submit": "simple_pos.pos_invoice.on_submit",
        "on_cancel": "simple_pos.pos_invoice.on_cancel",
    }
}

# App Includes
app_include_js = "/assets/simple_pos/js/pos.js"
app_include_css = "/assets/simple_pos/css/pos.css"

# Web Pages
website_generators = ["simple_pos.website_generator"]

# Permissions
permission_query_conditions = {
    "Sales Invoice": "simple_pos.pos_invoice.get_permission_query_conditions",
}

# DocType Class
doctype_list = [
    "POS Profile",
    "POS Invoice",
]

# Page Routes
page_routes = [
    {"page": "pos", "route": "pos"},
]

# Workspace
workspace = [
    {"name": "POS Workspace", "module": "Simple POS"},
]

# Reports
report_name = [
    "POS Sales Report",
    "POS Inventory Report",
]
