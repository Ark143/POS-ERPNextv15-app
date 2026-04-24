# Simple POS for ERPNext v15

A comprehensive Point of Sale (POS) application for ERPNext v15 that can be installed via Frappe Cloud.

## Features

- **Item Selection & Checkout**: Touch-friendly interface with barcode support
- **Customer Management**: Link to ERPNext Customer records
- **Payment Processing**: Multiple payment methods (cash, card, etc.)
- **Receipt Printing**: Thermal printer format
- **Inventory Integration**: Real-time stock validation and updates
- **Sales Reports**: Daily, weekly, and monthly sales analytics
- **ERPNext Integration**: Seamless integration with Items, Customers, Warehouses, and Accounting

## Installation

### Via Frappe Cloud

1. Go to your Frappe Cloud dashboard
2. Navigate to your site's marketplace
3. Search for "Simple POS"
4. Click "Install"

### Via Bench

```bash
bench get-app https://github.com/Ark143/POS-ERPNextv15-app
bench install-app simple_pos
bench build
bench restart
```

## Configuration

1. Create a **POS Profile** with your warehouse and payment methods
2. Assign the POS Profile to users
3. Start creating POS Invoices from the POS Workspace

## Usage

1. Navigate to the POS Workspace
2. Click "New POS Invoice"
3. Select customer and items
4. Process payment
5. Generate receipt

## License

MIT License
