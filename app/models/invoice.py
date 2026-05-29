from datetime import datetime, timezone
from beanie import Document, Indexed
from pydantic import Field

class Invoice(Document):
    invoice_number: Indexed(str, unique=True)
    company_id: Indexed(str)  # Reference to Company id
    amount: float
    status: Indexed(str) = "UNPAID"  # UNPAID, PAID, OVERDUE, CANCELLED
    due_date: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "invoices"

    class Config:
        json_schema_extra = {
            "example": {
                "invoice_number": "INV-2026-001",
                "company_id": "651a2345bc6789def0123456",
                "amount": 5000.00,
                "status": "UNPAID",
                "due_date": "2026-06-29T19:54:47Z",
                "created_at": "2026-05-29T19:54:47Z"
            }
        }
