from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from app.api.deps import get_current_active_user, RoleChecker, PermissionChecker
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.company import Company
from app.models.user import User
from app.schemas.platform import (
    InvoiceCreate, InvoiceResponse,
    PaymentCreate, PaymentResponse
)
from app.utils.audit import log_action

router = APIRouter()


@router.post("/invoices", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    invoice_in: InvoiceCreate,
    request: Request,
    current_user: User = Depends(PermissionChecker("manage_billing"))
) -> Any:
    """
    Generate a new workforce invoice for a client company.
    Requires 'manage_billing' permission.
    """
    # Verify company exists
    company = await Company.get(invoice_in.company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Company with ID {invoice_in.company_id} does not exist."
        )

    # Verify unique invoice number
    existing = await Invoice.find_one(Invoice.invoice_number == invoice_in.invoice_number)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invoice number {invoice_in.invoice_number} already exists."
        )

    invoice = Invoice(
        invoice_number=invoice_in.invoice_number,
        company_id=invoice_in.company_id,
        amount=invoice_in.amount,
        due_date=invoice_in.due_date,
    )
    await invoice.insert()
    
    await log_action(
        action="CREATE_INVOICE",
        details=f"Generated Invoice {invoice.invoice_number} for company {company.name} (Amount: {invoice.amount})",
        user=current_user,
        request=request
    )
    return invoice


@router.get("/invoices", response_model=List[InvoiceResponse])
async def list_invoices(
    skip: int = 0,
    limit: int = 100,
    status_filter: str = None,
    current_user: User = Depends(RoleChecker(["SUPER_ADMIN", "ADMIN"]))
) -> Any:
    """
    Fetch a paginated list of all invoices. Can filter by status (e.g. UNPAID, PAID).
    Accessible to admins.
    """
    query = {}
    if status_filter:
        query["status"] = status_filter
        
    return await Invoice.find(query).skip(skip).limit(limit).to_list()


@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: str,
    current_user: User = Depends(RoleChecker(["SUPER_ADMIN", "ADMIN"]))
) -> Any:
    """
    Fetch specific invoice details.
    """
    invoice = await Invoice.get(invoice_id)
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found",
        )
    return invoice


# ==============================================================================
# PAYMENTS TRACKING
# ==============================================================================

@router.post("/payments", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    payment_in: PaymentCreate,
    request: Request,
    current_user: User = Depends(PermissionChecker("manage_billing"))
) -> Any:
    """
    Record a new payment transaction against an outstanding invoice.
    Automatically transitions invoice status from UNPAID to PAID.
    """
    invoice = await Invoice.get(payment_in.invoice_id)
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invoice ID {payment_in.invoice_id} does not exist."
        )

    payment = Payment(
        invoice_id=payment_in.invoice_id,
        amount=payment_in.amount,
        payment_method=payment_in.payment_method,
        transaction_id=payment_in.transaction_id,
        status="SUCCESS"
    )
    await payment.insert()

    # Automatically transition invoice status
    invoice.status = "PAID"
    await invoice.save()
    
    await log_action(
        action="RECORD_PAYMENT",
        details=f"Recorded payment of {payment.amount} for invoice {invoice.invoice_number}. Invoice status set to PAID.",
        user=current_user,
        request=request
    )
    return payment


@router.get("/payments", response_model=List[PaymentResponse])
async def list_payments(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(RoleChecker(["SUPER_ADMIN", "ADMIN"]))
) -> Any:
    """
    Fetch paginated historical payment transactions.
    """
    return await Payment.find_all().skip(skip).limit(limit).to_list()
