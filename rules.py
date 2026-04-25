# ---------------------------
# Rule catalog
# ---------------------------
rule_catalog = [
    {
        "rule_id": "INV-001",
        "name": "Invoice number required",
        "severity": "HIGH",
        "category": "Required Fields",
        "description": "Invoice number must be provided."
    },
    {
        "rule_id": "INV-002",
        "name": "Supplier ID required",
        "severity": "HIGH",
        "category": "Required Fields",
        "description": "Supplier ID must be provided."
    },
    {
        "rule_id": "INV-003",
        "name": "At least one line item required",
        "severity": "HIGH",
        "category": "Required Fields",
        "description": "Invoice must contain at least one line item."
    },
    {
        "rule_id": "INV-004",
        "name": "Line amount calculation check",
        "severity": "MEDIUM",
        "category": "Arithmetic",
        "description": "Line amount should match quantity multiplied by unit price."
    },
    {
        "rule_id": "INV-005",
        "name": "Header total check",
        "severity": "HIGH",
        "category": "Arithmetic",
        "description": "Invoice header amount should match the sum of all line amounts."
    },
    {
        "rule_id": "INV-006",
        "name": "Quantity must be positive",
        "severity": "HIGH",
        "category": "Line Validation",
        "description": "Invoice quantity must be greater than zero."
    },
    {
        "rule_id": "INV-007",
        "name": "Unit price cannot be negative",
        "severity": "HIGH",
        "category": "Line Validation",
        "description": "Invoice unit price cannot be negative."
    },
    {
        "rule_id": "INV-008",
        "name": "Line amount cannot be negative",
        "severity": "HIGH",
        "category": "Line Validation",
        "description": "Invoice line amount cannot be negative."
    },
    {
        "rule_id": "INV-009",
        "name": "Duplicate invoice check",
        "severity": "HIGH",
        "category": "Duplicate Detection",
        "description": "Invoice number and supplier combination should not already exist."
    },
    {
        "rule_id": "INV-010",
        "name": "Supplier must exist",
        "severity": "HIGH",
        "category": "Supplier Validation",
        "description": "Supplier must exist in supplier master data."
    },
    {
        "rule_id": "INV-011",
        "name": "Supplier must not be blocked",
        "severity": "HIGH",
        "category": "Supplier Validation",
        "description": "Blocked suppliers should not be allowed."
    },
    {
        "rule_id": "INV-012",
        "name": "Supplier must be active",
        "severity": "HIGH",
        "category": "Supplier Validation",
        "description": "Inactive suppliers should not be allowed."
    },
    {
        "rule_id": "INV-013",
        "name": "PO must exist",
        "severity": "HIGH",
        "category": "PO Validation",
        "description": "Purchase order number must exist."
    },
    {
        "rule_id": "INV-014",
        "name": "Supplier must match PO",
        "severity": "HIGH",
        "category": "PO Validation",
        "description": "Supplier on invoice must match supplier on purchase order."
    },
    {
        "rule_id": "INV-015",
        "name": "PO line must exist",
        "severity": "HIGH",
        "category": "PO Validation",
        "description": "Referenced purchase order line must exist."
    },
    {
        "rule_id": "INV-016",
        "name": "Quantity cannot exceed PO open quantity",
        "severity": "HIGH",
        "category": "PO Validation",
        "description": "Invoice quantity should not exceed open purchase order quantity."
    },
    {
        "rule_id": "INV-017",
        "name": "Price variance check",
        "severity": "MEDIUM",
        "category": "PO Validation",
        "description": "Invoice unit price should match purchase order unit price."
    }
]

# ---------------------------
# Mock invoice history
# ---------------------------
existing_invoices = [
    {
        "invoice_number": "INV-1001",
        "supplier_id": "SUP-100",
        "header_amount": 200
    },
    {
        "invoice_number": "INV-2001",
        "supplier_id": "SUP-200",
        "header_amount": 500
    }
]

# ---------------------------
# Mock supplier master
# ---------------------------
supplier_master = {
    "SUP-100": {
        "name": "ABC Supplies",
        "status": "ACTIVE"
    },
    "SUP-200": {
        "name": "XYZ Traders",
        "status": "BLOCKED"
    },
    "SUP-300": {
        "name": "Global Parts",
        "status": "INACTIVE"
    }
}

# ---------------------------
# Mock purchase orders
# ---------------------------
purchase_orders = {
    "PO-1001": {
        "supplier_id": "SUP-100",
        "lines": {
            10: {
                "open_quantity": 5,
                "unit_price": 100.0
            },
            20: {
                "open_quantity": 3,
                "unit_price": 50.0
            }
        }
    },
    "PO-2001": {
        "supplier_id": "SUP-200",
        "lines": {
            10: {
                "open_quantity": 2,
                "unit_price": 250.0
            }
        }
    }
}