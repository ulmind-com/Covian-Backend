import csv
import io
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from app.api.deps import RoleChecker, PermissionChecker
from app.models.user import User
from app.models.job import Job
from app.models.lead import Lead
from app.models.invoice import Invoice
from app.models.audit_log import AuditLog
from app.schemas.platform import DashboardKPIs, AuditLogResponse

router = APIRouter()


@router.get("/dashboard/kpi", response_model=DashboardKPIs)
async def get_dashboard_kpis(
    current_user: User = Depends(RoleChecker(["SUPER_ADMIN", "ADMIN"]))
) -> Any:
    """
    Fetch global KPI metrics for the CoreVita Admin Dashboard.
    Performs high-performance counts and aggregates payment revenue directly from MongoDB.
    """
    total_users = await User.count()
    total_jobs = await Job.count()
    total_leads = await Lead.count()
    
    new_leads_count = await Lead.find(Lead.status == "NEW").count()
    open_jobs_count = await Job.find(Job.status == "OPEN").count()

    # Calculate total revenue using high-performance MongoDB aggregation pipelines
    revenue_pipeline = [
        {"$match": {"status": "PAID"}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]
    revenue_agg = await Invoice.aggregate(revenue_pipeline).to_list()
    total_revenue = float(revenue_agg[0]["total"]) if revenue_agg else 0.0

    return {
        "total_users": total_users,
        "total_jobs": total_jobs,
        "total_revenue": total_revenue,
        "total_leads": total_leads,
        "new_leads_count": new_leads_count,
        "open_jobs_count": open_jobs_count,
    }


@router.get("/audit-logs", response_model=List[AuditLogResponse])
async def get_activity_audit_logs(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(RoleChecker(["SUPER_ADMIN", "ADMIN"]))
) -> Any:
    """
    Retrieve historical platform administrative and action audit logs.
    Accessible only to SUPER_ADMIN and ADMIN.
    """
    return await AuditLog.find_all().sort("-created_at").skip(skip).limit(limit).to_list()


@router.get("/reports/export-invoices-csv")
async def export_invoices_report_csv(
    current_user: User = Depends(PermissionChecker("view_reports"))
) -> StreamingResponse:
    """
    Compile and stream a custom CSV report of all invoices registered on the platform.
    Requires 'view_reports' permission.
    """
    invoices = await Invoice.find_all().to_list()
    
    # Generate CSV stream in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        "Invoice ID", 
        "Invoice Number", 
        "Company ID", 
        "Amount (USD)", 
        "Status", 
        "Due Date", 
        "Created At"
    ])
    
    # Content rows
    for invoice in invoices:
        writer.writerow([
            str(invoice.id),
            invoice.invoice_number,
            invoice.company_id,
            invoice.amount,
            invoice.status,
            invoice.due_date.strftime("%Y-%m-%d %H:%M:%S"),
            invoice.created_at.strftime("%Y-%m-%d %H:%M:%S")
        ])
        
    output.seek(0)
    
    # Stream the file back immediately to the admin's browser
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=corevita_invoices_report.csv"}
    )
