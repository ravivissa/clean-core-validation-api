from pydantic import BaseModel, Field
from typing import List


class InvoiceItem(BaseModel):
    line_no: int = Field(..., description="Invoice line number", example=1)
    po_line: int = Field(..., description="Referenced purchase order line number", example=10)
    quantity: float = Field(..., description="Invoiced quantity", example=2)
    unit_price: float = Field(..., description="Unit price on the invoice", example=100)
    line_amount: float = Field(..., description="Total amount for this line", example=200)


class Invoice(BaseModel):
    invoice_number: str = Field(..., description="Supplier invoice number", example="INV-7001")
    supplier_id: str = Field(..., description="Supplier identifier", example="SUP-100")
    po_number: str = Field(..., description="Referenced purchase order number", example="PO-1001")
    header_amount: float = Field(..., description="Invoice header total amount", example=200)
    items: List[InvoiceItem] = Field(..., description="Invoice line items")