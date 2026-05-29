from datetime import datetime, timezone
from typing import Optional
from beanie import Document, Indexed
from pydantic import Field

class Payment(Document):
    invoice_id: Indexed(str)  # Reference to Invoice id
    amount: float
    payment_method: str = "STRIPE"  # STRIPE, BANK_TRANSFER
    transaction_id: Optional[str] = None
    status: Indexed(str) = "SUCCESS"  # PENDING, SUCCESS, FAILED
    paid_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "payments"

    class Config:
        json_schema_extra = {
            "example": {
                "invoice_id": "651a2345bc6789def0123459",
                "amount": 5000.00,
                "payment_method": "STRIPE",
                "transaction_id": "ch_3M4yqT2eZvKYlo2C",
                "status": "SUCCESS",
                "paid_at": "2026-05-29T19:54:47Z"
            }
        }
