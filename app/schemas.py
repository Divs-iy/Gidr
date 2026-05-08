from pydantic import BaseModel
from typing import List, Optional

class InvoiceData(BaseModel):
    invoice_number: Optional[str] = None
    vendor_name: Optional[str] = None
    date: Optional[str] = None
    gstin: Optional[str] = None
    total_amount: Optional[float] = 0.0
    tax_amount: Optional[float] = 0.0
    confidence_score: float = 0.0

class ProcessingResponse(BaseModel):
    status: str
    filename: str
    extracted_data: InvoiceData