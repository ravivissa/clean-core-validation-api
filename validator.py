from rules import (
    existing_invoices,
    supplier_master,
    purchase_orders
)


def run_invoice_validation(invoice):
    errors = []
    warnings = []
    passed_rules = []

    def add_issue(rule_id, severity, message):
        issue = {
            "rule_id": rule_id,
            "severity": severity,
            "message": message
        }

        if severity == "HIGH":
            errors.append(issue)
        elif severity == "MEDIUM":
            warnings.append(issue)

    if not invoice.invoice_number:
        add_issue("INV-001", "HIGH", "Invoice number is missing")
    else:
        passed_rules.append("INV-001")

    if not invoice.supplier_id:
        add_issue("INV-002", "HIGH", "Supplier ID is missing")
    else:
        passed_rules.append("INV-002")

    if len(invoice.items) == 0:
        add_issue("INV-003", "HIGH", "No line items found")
    else:
        passed_rules.append("INV-003")

    duplicate_found = False
    for old in existing_invoices:
        if (
            old["invoice_number"] == invoice.invoice_number
            and old["supplier_id"] == invoice.supplier_id
        ):
            duplicate_found = True
            break

    if duplicate_found:
        add_issue("INV-009", "HIGH", "Duplicate invoice detected")
    else:
        passed_rules.append("INV-009")

    if invoice.supplier_id not in supplier_master:
        add_issue("INV-010", "HIGH", "Supplier not found in supplier master")
    else:
        passed_rules.append("INV-010")

        supplier_status = supplier_master[invoice.supplier_id]["status"]

        if supplier_status == "BLOCKED":
            add_issue("INV-011", "HIGH", "Supplier is blocked")
        else:
            passed_rules.append("INV-011")

        if supplier_status == "INACTIVE":
            add_issue("INV-012", "HIGH", "Supplier is inactive")
        elif supplier_status == "ACTIVE":
            passed_rules.append("INV-012")

    if invoice.po_number not in purchase_orders:
        add_issue("INV-013", "HIGH", "PO number not found")
    else:
        passed_rules.append("INV-013")
        po_data = purchase_orders[invoice.po_number]

        if po_data["supplier_id"] != invoice.supplier_id:
            add_issue("INV-014", "HIGH", "Supplier does not match PO supplier")
        else:
            passed_rules.append("INV-014")

        for item in invoice.items:
            if item.po_line not in po_data["lines"]:
                add_issue("INV-015", "HIGH", f"PO line {item.po_line} not found")
            else:
                passed_rules.append("INV-015")
                po_line_data = po_data["lines"][item.po_line]

                if item.quantity > po_line_data["open_quantity"]:
                    add_issue("INV-016", "HIGH", f"Line {item.line_no}: quantity exceeds PO open quantity")
                else:
                    passed_rules.append("INV-016")

                if abs(item.unit_price - po_line_data["unit_price"]) > 0.01:
                    add_issue("INV-017", "MEDIUM", f"Line {item.line_no}: unit price differs from PO price")
                else:
                    passed_rules.append("INV-017")

    for item in invoice.items:
        calculated = item.quantity * item.unit_price
        if abs(calculated - item.line_amount) > 0.01:
            add_issue("INV-004", "MEDIUM", f"Line {item.line_no}: amount mismatch")
        else:
            passed_rules.append("INV-004")

        if item.quantity <= 0:
            add_issue("INV-006", "HIGH", f"Line {item.line_no}: quantity must be greater than 0")
        else:
            passed_rules.append("INV-006")

        if item.unit_price < 0:
            add_issue("INV-007", "HIGH", f"Line {item.line_no}: unit price cannot be negative")
        else:
            passed_rules.append("INV-007")

        if item.line_amount < 0:
            add_issue("INV-008", "HIGH", f"Line {item.line_no}: line amount cannot be negative")
        else:
            passed_rules.append("INV-008")

    total = sum(item.line_amount for item in invoice.items)
    if abs(total - invoice.header_amount) > 0.01:
        add_issue("INV-005", "HIGH", "Header amount does not match sum of items")
    else:
        passed_rules.append("INV-005")

    passed_rules = sorted(list(set(passed_rules)))

    total_issues = len(errors) + len(warnings)

    if total_issues == 0:
        status = "PASS"
        score = 100
        recommended_action = "AUTO_POST"
        queue = "AUTO_POST_READY"
        summary = "Invoice is valid and ready for posting."
    else:
        score = 100 - (len(errors) * 15) - (len(warnings) * 5)
        if score < 0:
            score = 0

        if len(errors) > 0:
            status = "FAIL"
            recommended_action = "REJECT_OR_REVIEW"
            queue = "AP_REVIEW"
            summary = "Invoice has critical issues and requires review."
        else:
            status = "REVIEW"
            recommended_action = "REVIEW"
            queue = "AP_REVIEW"
            summary = "Invoice has minor issues and should be reviewed."

    result = {
        "invoice_number": invoice.invoice_number,
        "supplier_id": invoice.supplier_id,
        "po_number": invoice.po_number,
        "status": status,
        "score": score,
        "summary": summary,
        "decision": {
            "recommended_action": recommended_action,
            "queue": queue
        },
        "errors": errors,
        "warnings": warnings,
        "passed_rules": passed_rules
    }

    return result