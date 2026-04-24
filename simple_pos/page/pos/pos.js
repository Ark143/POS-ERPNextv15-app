frappe.pages['pos'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Point of Sale',
        single_column: true
    });
    
    let $container = $(
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
    );
    
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
                    $select.append(<option value="${customer.name}">${customer.customer_name}</option>);
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
        let $item = $(
            <div class="pos-item" data-item-code="${item.item_code}">
                <div class="pos-item-image">
                    ${item.image ? <img src="${item.image}" /> : '<div class="no-image">No Image</div>'}
                </div>
                <div class="pos-item-name">${item.item_name}</div>
                <div class="pos-item-price">Stock: ${item.stock_qty}</div>
            </div>
        );
        
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
        
        let $row = $(
            <div class="cart-item">
                <div class="cart-item-name">${item.item_name}</div>
                <div class="cart-item-qty">
                    <button class="btn btn-sm" onclick="update_qty(${index}, -1)">-</button>
                    <span>${item.qty}</span>
                    <button class="btn btn-sm" onclick="update_qty(${index}, 1)">+</button>
                </div>
                <div class="cart-item-amount">${amount.toFixed(2)}</div>
            </div>
        );
        
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
