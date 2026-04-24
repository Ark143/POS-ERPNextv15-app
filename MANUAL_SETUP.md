# Manual Setup Guide for Simple POS App

Due to technical issues with file creation, please create the following files manually with the provided contents.

## API Files

### `simple_pos/api/__init__.py`
```python
```

### `simple_pos/api/pos_api.py`
```python
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
```

## Page Files

### `simple_pos/page/pos/pos.js`
```javascript
frappe.pages['pos'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Point of Sale',
        single_column: true
    });
    
    let $container = $(`
        <div class="pos-container">
            <div class="pos-layout">
                <div class="pos-items-section">
                    <div class="pos-search">
                        <input type="text" id="pos-search" placeholder="Search items..." />
                    </div>
                    <div class="pos-items-grid" id="pos-items-grid"></div>
                </div>
                <div class="pos-cart-section">
                    <div class="pos-customer-select">
                        <label>Customer:</label>
                        <select id="pos-customer"></select>
                    </div>
                    <div class="pos-cart-items" id="pos-cart-items"></div>
                    <div class="pos-totals">
                        <div class="total-row">
                            <span>Subtotal:</span>
                            <span id="pos-subtotal">0.00</span>
                        </div>
                        <div class="total-row">
                            <span>Tax:</span>
                            <span id="pos-tax">0.00</span>
                        </div>
                        <div class="total-row grand-total">
                            <span>Total:</span>
                            <span id="pos-total">0.00</span>
                        </div>
                    </div>
                    <div class="pos-payment">
                        <button class="btn btn-primary btn-lg" id="pos-checkout">Checkout</button>
                    </div>
                </div>
            </div>
        </div>
    `);
    
    $(page.main).find('.page-content').html($container);
    
    // Load initial data
    load_pos_data();
    
    // Event handlers
    $('#pos-search').on('input', debounce(function() {
        search_items($(this).val());
    }, 300));
    
    $('#pos-checkout').on('click', function() {
        checkout();
    });
}

function load_pos_data() {
    frappe.call({
        method: 'simple_pos.api.get_pos_profiles',
        callback: function(r) {
            if (r.message) {
                window.pos_profiles = r.message;
                if (r.message.length > 0) {
                    window.current_pos_profile = r.message[0].name;
                    load_items();
                }
            }
        }
    });
    
    frappe.call({
        method: 'simple_pos.api.get_customers',
        callback: function(r) {
            if (r.message) {
                let $select = $('#pos-customer');
                $select.empty();
                $select.append('<option value="">Select Customer</option>');
                r.message.forEach(customer => {
                    $select.append(`<option value="${customer.name}">${customer.customer_name}</option>`);
                });
            }
        }
    });
}

function load_items() {
    frappe.call({
        method: 'simple_pos.api.get_items',
        args: { pos_profile: window.current_pos_profile },
        callback: function(r) {
            if (r.message) {
                render_items(r.message);
            }
        }
    });
}

function render_items(items) {
    let $grid = $('#pos-items-grid');
    $grid.empty();
    
    items.forEach(item => {
        let $item = $(`
            <div class="pos-item" data-item-code="${item.item_code}">
                <div class="pos-item-image">
                    ${item.image ? `<img src="${item.image}" />` : '<div class="no-image">No Image</div>'}
                </div>
                <div class="pos-item-name">${item.item_name}</div>
                <div class="pos-item-price">Stock: ${item.stock_qty}</div>
            </div>
        `);
        
        $item.on('click', function() {
            add_to_cart(item);
        });
        
        $grid.append($item);
    });
}

function add_to_cart(item) {
    if (!window.cart) {
        window.cart = [];
    }
    
    let existing = window.cart.find(c => c.item_code === item.item_code);
    if (existing) {
        existing.qty += 1;
    } else {
        window.cart.push({
            item_code: item.item_code,
            item_name: item.item_name,
            qty: 1,
            rate: 0 // Will be fetched from item price
        });
    }
    
    render_cart();
}

function render_cart() {
    let $cart = $('#pos-cart-items');
    $cart.empty();
    
    let subtotal = 0;
    
    window.cart.forEach((item, index) => {
        let amount = item.qty * item.rate;
        subtotal += amount;
        
        let $row = $(`
            <div class="cart-item">
                <div class="cart-item-name">${item.item_name}</div>
                <div class="cart-item-qty">
                    <button class="btn btn-sm" onclick="update_qty(${index}, -1)">-</button>
                    <span>${item.qty}</span>
                    <button class="btn btn-sm" onclick="update_qty(${index}, 1)">+</button>
                </div>
                <div class="cart-item-amount">${amount.toFixed(2)}</div>
            </div>
        `);
        
        $cart.append($row);
    });
    
    $('#pos-subtotal').text(subtotal.toFixed(2));
    $('#pos-tax').text('0.00');
    $('#pos-total').text(subtotal.toFixed(2));
}

function update_qty(index, change) {
    window.cart[index].qty += change;
    if (window.cart[index].qty <= 0) {
        window.cart.splice(index, 1);
    }
    render_cart();
}

function checkout() {
    if (!window.cart || window.cart.length === 0) {
        frappe.msgprint('Please add items to cart');
        return;
    }
    
    let customer = $('#pos-customer').val();
    if (!customer) {
        frappe.msgprint('Please select a customer');
        return;
    }
    
    frappe.call({
        method: 'simple_pos.api.create_invoice',
        args: {
            data: {
                customer: customer,
                items: window.cart,
                pos_profile: window.current_pos_profile
            }
        },
        callback: function(r) {
            if (r.message) {
                frappe.msgprint('Invoice created: ' + r.message);
                window.cart = [];
                render_cart();
            }
        }
    });
}

function search_items(text) {
    frappe.call({
        method: 'simple_pos.api.get_items',
        args: { 
            pos_profile: window.current_pos_profile,
            search_text: text
        },
        callback: function(r) {
            if (r.message) {
                render_items(r.message);
            }
        }
    });
}

function debounce(func, wait) {
    let timeout;
    return function() {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, arguments), wait);
    };
}
```

### `simple_pos/page/pos/pos.html`
```html
{% extends "templates/base.html" %}

{% block page_content %}
<div id="pos-page"></div>
{% endblock %}
```

### `simple_pos/page/pos/pos.css`
```css
.pos-container {
    padding: 20px;
    height: calc(100vh - 100px);
}

.pos-layout {
    display: flex;
    gap: 20px;
    height: 100%;
}

.pos-items-section {
    flex: 2;
    display: flex;
    flex-direction: column;
}

.pos-search input {
    width: 100%;
    padding: 10px;
    font-size: 16px;
    border: 1px solid #d1d8dd;
    border-radius: 4px;
    margin-bottom: 20px;
}

.pos-items-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: 15px;
    overflow-y: auto;
    flex: 1;
}

.pos-item {
    border: 1px solid #d1d8dd;
    border-radius: 8px;
    padding: 10px;
    cursor: pointer;
    transition: all 0.2s;
}

.pos-item:hover {
    border-color: #3498db;
    box-shadow: 0 2px 8px rgba(52, 152, 219, 0.2);
}

.pos-item-image {
    height: 100px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #f7fafc;
    border-radius: 4px;
    margin-bottom: 10px;
}

.pos-item-image img {
    max-width: 100%;
    max-height: 100%;
    object-fit: contain;
}

.no-image {
    color: #8d99a6;
    font-size: 12px;
}

.pos-item-name {
    font-weight: 600;
    margin-bottom: 5px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.pos-item-price {
    font-size: 14px;
    color: #566576;
}

.pos-cart-section {
    flex: 1;
    background: #f7fafc;
    border-radius: 8px;
    padding: 20px;
    display: flex;
    flex-direction: column;
}

.pos-customer-select {
    margin-bottom: 20px;
}

.pos-customer-select select {
    width: 100%;
    padding: 8px;
    border: 1px solid #d1d8dd;
    border-radius: 4px;
}

.pos-cart-items {
    flex: 1;
    overflow-y: auto;
    margin-bottom: 20px;
}

.cart-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px;
    background: white;
    border-radius: 4px;
    margin-bottom: 10px;
}

.cart-item-name {
    flex: 1;
    font-weight: 500;
}

.cart-item-qty {
    display: flex;
    align-items: center;
    gap: 10px;
}

.cart-item-amount {
    font-weight: 600;
    min-width: 80px;
    text-align: right;
}

.pos-totals {
    margin-bottom: 20px;
}

.total-row {
    display: flex;
    justify-content: space-between;
    padding: 5px 0;
}

.grand-total {
    font-size: 18px;
    font-weight: 700;
    border-top: 2px solid #d1d8dd;
    padding-top: 10px;
    margin-top: 10px;
}

.pos-payment button {
    width: 100%;
    padding: 15px;
    font-size: 18px;
    font-weight: 600;
}
```

## Report Files

### `simple_pos/report/pos_sales_report/pos_sales_report.py`
```python
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
        FROM `tabSales Invoice` si
        INNER JOIN `tabSales Invoice Item` sii ON si.name = sii.parent
        LEFT JOIN `tabSales Invoice Payment` sip ON si.name = sip.parent
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
```

### `simple_pos/report/pos_sales_report/pos_sales_report.json`
```json
{
 "add_total_row": 0,
 "creation": "2024-04-24 00:00:00.000000",
 "disable_prepared_report": 0,
 "disabled": 0,
 "doc_type": "Sales Invoice",
 "docstatus": 0,
 "idx": 0,
 "is_standard": "Yes",
 "letter_head": null,
 "modified": "2024-04-24 00:00:00.000000",
 "modified_by": "Administrator",
 "module": "Simple POS",
 "name": "POS Sales Report",
 "owner": "Administrator",
 "prepared_report": 0,
 "ref_doctype": "Sales Invoice",
 "report_name": "POS Sales Report",
 "report_type": "Script Report",
 "roles": [
  {
   "role": "POS Manager"
  },
  {
   "role": "POS User"
  },
  {
   "role": "System Manager"
  }
 ]
}
```

## Print Format Files

### `simple_pos/print_format/pos_receipt/pos_receipt.json`
```json
{
 "creation": "2024-04-24 00:00:00.000000",
 "custom_format": 0,
 "default_print_format": 0,
 "disabled": 0,
 "doc_type": "Sales Invoice",
 "idx": 0,
 "modified": "2024-04-24 00:00:00.000000",
 "modified_by": "Administrator",
 "module": "Simple POS",
 "name": "POS Receipt",
 "owner": "Administrator",
 "print_format_builder": 0,
 "print_format_type": "Server",
 "raw_printing": 0,
 "standard": "Yes"
}
```

### `simple_pos/print_format/pos_receipt/pos_receipt.html`
```html
<style>
    .pos-receipt {
        font-family: 'Courier New', monospace;
        font-size: 12px;
        width: 80mm;
        padding: 5mm;
    }
    .pos-receipt-header {
        text-align: center;
        margin-bottom: 10px;
    }
    .pos-receipt-header h2 {
        margin: 0;
        font-size: 16px;
    }
    .pos-receipt-header p {
        margin: 5px 0;
        font-size: 10px;
    }
    .pos-receipt-divider {
        border-top: 1px dashed #000;
        margin: 10px 0;
    }
    .pos-receipt-item {
        display: flex;
        justify-content: space-between;
        margin: 5px 0;
    }
    .pos-receipt-item-name {
        flex: 1;
    }
    .pos-receipt-item-qty {
        text-align: center;
        width: 50px;
    }
    .pos-receipt-item-amount {
        text-align: right;
        width: 80px;
    }
    .pos-receipt-totals {
        margin-top: 10px;
    }
    .pos-receipt-total {
        display: flex;
        justify-content: space-between;
        margin: 5px 0;
    }
    .pos-receipt-grand-total {
        font-weight: bold;
        font-size: 14px;
        border-top: 1px solid #000;
        padding-top: 5px;
    }
    .pos-receipt-footer {
        text-align: center;
        margin-top: 15px;
        font-size: 10px;
    }
</style>

<div class="pos-receipt">
    <div class="pos-receipt-header">
        <h2>{{ doc.company }}</h2>
        <p>{{ frappe.db.get_value("Company", doc.company, "address") }}</p>
        <p>Tel: {{ frappe.db.get_value("Company", doc.company, "phone_no") }}</p>
    </div>
    
    <div class="pos-receipt-divider"></div>
    
    <div>
        <p><strong>Invoice:</strong> {{ doc.name }}</p>
        <p><strong>Date:</strong> {{ doc.posting_date }}</p>
        <p><strong>Customer:</strong> {{ doc.customer_name }}</p>
    </div>
    
    <div class="pos-receipt-divider"></div>
    
    <div class="pos-receipt-items">
        {% for item in doc.items %}
        <div class="pos-receipt-item">
            <div class="pos-receipt-item-name">{{ item.item_name }}</div>
            <div class="pos-receipt-item-qty">{{ item.qty }}</div>
            <div class="pos-receipt-item-amount">{{ item.amount }}</div>
        </div>
        {% endfor %}
    </div>
    
    <div class="pos-receipt-divider"></div>
    
    <div class="pos-receipt-totals">
        <div class="pos-receipt-total">
            <span>Subtotal:</span>
            <span>{{ doc.subtotal }}</span>
        </div>
        <div class="pos-receipt-total">
            <span>Tax:</span>
            <span>{{ doc.total_taxes_and_charges }}</span>
        </div>
        <div class="pos-receipt-total pos-receipt-grand-total">
            <span>TOTAL:</span>
            <span>{{ doc.grand_total }}</span>
        </div>
    </div>
    
    <div class="pos-receipt-divider"></div>
    
    <div>
        <p><strong>Payment Method:</strong> {{ doc.mode_of_payment }}</p>
        <p><strong>Paid Amount:</strong> {{ doc.paid_amount }}</p>
    </div>
    
    <div class="pos-receipt-footer">
        <p>Thank you for your purchase!</p>
        <p>{{ frappe.utils.now() }}</p>
    </div>
</div>
```

## Workspace Files

### `simple_pos/workspace/pos_workspace/pos_workspace.json`
```json
{
 "category": "Simple POS",
 "charts": [],
 "creation": "2024-04-24 00:00:00.000000",
 "doc_type": "POS Profile",
 "extends_another_page": 0,
 "forbidden_doctypes": [],
 "idx": 0,
 "is_standard": 1,
 "label": "POS Workspace",
 "links": [
  {
   "hidden": 0,
   "is_query_report": 0,
   "label": "POS Profile",
   "link_count": 0,
   "link_to": "POS Profile",
   "link_type": "DocType",
   "onboard": 0,
   "type": "Link"
  },
  {
   "hidden": 0,
   "is_query_report": 0,
   "label": "POS Invoice",
   "link_count": 0,
   "link_to": "Sales Invoice",
   "link_type": "DocType",
   "onboard": 0,
   "type": "Link"
  },
  {
   "hidden": 0,
   "is_query_report": 0,
   "label": "POS Sales Report",
   "link_count": 0,
   "link_to": "POS Sales Report",
   "link_type": "Report",
   "onboard": 0,
   "type": "Link"
  },
  {
   "hidden": 0,
   "is_query_report": 0,
   "label": "POS",
   "link_count": 0,
   "link_to": "pos",
   "link_type": "Page",
   "onboard": 0,
   "type": "Link"
  }
 ],
 "modified": "2024-04-24 00:00:00.000000",
 "modified_by": "Administrator",
 "module": "Simple POS",
 "name": "POS Workspace",
 "owner": "Administrator",
 "parent_page": "",
 "quick_lists": [],
 "shortcuts": [
  {
   "description": "Create new POS Invoice",
   "doc_view": "List",
   "label": "New POS Invoice",
   "link_to": "Sales Invoice",
   "type": "DocType"
  }
 ]
}
```

## Additional Files

### `.gitignore`
```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Frappe
*.pyc
node_modules/
public/build/
public/css/
public/js/
public/fonts/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db
```

### `LICENSE`
```
MIT License

Copyright (c) 2024 Ark143

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Git Setup Commands

**Note: Git must be installed first. Download from https://git-scm.com/download/win**

After creating all files, run these commands in the app directory:

```bash
cd C:\Users\josem\simple_pos_app
git init
git add .
git commit -m "Initial commit: Simple POS app for ERPNext v15"
git branch -M main
git remote add origin https://github.com/Ark143/POS-ERPNextv15-app.git
git push -u origin main
```

## Installation Instructions

1. Clone the repository to your Frappe bench apps directory:
```bash
cd /path/to/frappe-bench/apps
git clone https://github.com/Ark143/POS-ERPNextv15-app.git simple_pos
```

2. Install the app:
```bash
bench install-app simple_pos
bench build
bench restart
```

3. Configure the app:
- Create a POS Profile
- Assign POS Profile to users
- Access the POS Workspace
