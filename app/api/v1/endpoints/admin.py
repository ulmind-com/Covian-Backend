"""
Admin Intelligence Endpoints
==============================
Provides AI-powered analytics, candidate matching, activity feed,
workflow management, and hiring analytics endpoints.

Routes:
  GET  /admin/matching/{job_id}         - AI candidate ranking
  GET  /admin/analytics/hiring          - Smart hiring analytics
  GET  /admin/activity-feed             - Real-time system activity feed
  POST /admin/workflows                 - Create automation rule
  GET  /admin/workflows                 - List automation rules
  GET  /admin/workflows/{id}            - Get single rule
  PUT  /admin/workflows/{id}            - Update automation rule
  DELETE /admin/workflows/{id}          - Delete automation rule
"""
from typing import Any, List, Optional
from datetime import datetime, timezone
import csv
import io
from fastapi import APIRouter, Depends, HTTPException, Query, status, Response
from fastapi.responses import StreamingResponse

from app.api.deps import RoleChecker, PermissionChecker
from app.models.user import User
from app.models.job import Job
from app.models.candidate import Candidate
from app.models.application import Application
from app.models.lead import Lead
from app.models.invoice import Invoice
from app.models.audit_log import AuditLog
from app.models.activity_log import ActivityLog
from app.models.workflow import WorkflowRule
from app.schemas.platform import (
    DashboardKPIs,
    AuditLogResponse,
    CandidateMatchResponse,
    CandidateMatchScore,
    HiringAnalyticsResponse,
    StageAnalytics,
    RecruiterPerformance,
    ActivityLogResponse,
    WorkflowRuleCreate,
    WorkflowRuleUpdate,
    WorkflowRuleResponse,
)

router = APIRouter()


# ──────────────────────────────────────────────────────────────────────────────
# 0. ORIGINAL ADMIN: DASHBOARD KPIs, AUDIT LOGS, CSV EXPORT
# ──────────────────────────────────────────────────────────────────────────────

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
    """Retrieve historical platform administrative and action audit logs."""
    return await AuditLog.find_all().sort("-created_at").skip(skip).limit(limit).to_list()


@router.get("/reports/export-invoices-csv")
async def export_invoices_report_csv(
    current_user: User = Depends(PermissionChecker("view_reports"))
) -> StreamingResponse:
    """Compile and stream a CSV report of all invoices registered on the platform."""
    invoices = await Invoice.find_all().to_list()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Invoice ID", "Invoice Number", "Company ID", "Amount (USD)", "Status", "Due Date", "Created At"])
    for invoice in invoices:
        writer.writerow([
            str(invoice.id), invoice.invoice_number, invoice.company_id,
            invoice.amount, invoice.status,
            invoice.due_date.strftime("%Y-%m-%d %H:%M:%S"),
            invoice.created_at.strftime("%Y-%m-%d %H:%M:%S")
        ])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=corevita_invoices_report.csv"}
    )



# ──────────────────────────────────────────────────────────────────────────────
# 1. AI CANDIDATE MATCHING
# ──────────────────────────────────────────────────────────────────────────────

def _compute_candidate_score(
    candidate: Candidate,
    job_skills: List[str],
    job_description_keywords: List[str],
) -> CandidateMatchScore:
    """
    Weighted scoring algorithm:
      - Skills match      : 60%  (how many required skills candidate has)
      - Keyword match     : 25%  (job description keywords found in candidate skills/name)
      - Availability bonus: 15%  (AVAILABLE = full bonus, PLACED = 0, INACTIVE = 0)

    Returns a CandidateMatchScore with per-component breakdown.
    """
    candidate_skills_lower = [s.lower() for s in candidate.skills]
    job_skills_lower = [s.lower() for s in job_skills]
    keywords_lower = [k.lower() for k in job_description_keywords]

    # ── Skills component ──────────────────────────────────────────────────────
    matched = [s for s in job_skills_lower if s in candidate_skills_lower]
    missing = [s for s in job_skills_lower if s not in candidate_skills_lower]
    skill_score = (len(matched) / len(job_skills_lower) * 100) if job_skills_lower else 50.0

    # ── Keyword component ─────────────────────────────────────────────────────
    candidate_text = " ".join(candidate_skills_lower + [candidate.name.lower()])
    keyword_hits = sum(1 for kw in keywords_lower if kw in candidate_text)
    keyword_score = (keyword_hits / len(keywords_lower) * 100) if keywords_lower else 50.0

    # ── Availability component ────────────────────────────────────────────────
    availability_score = 100.0 if candidate.status == "AVAILABLE" else 0.0

    # ── Weighted total ────────────────────────────────────────────────────────
    total = (skill_score * 0.60) + (keyword_score * 0.25) + (availability_score * 0.15)

    return CandidateMatchScore(
        candidate_id=str(candidate.id),
        candidate_name=candidate.name,
        candidate_email=candidate.email,
        skills=candidate.skills,
        status=candidate.status,
        total_score=round(total, 2),
        skill_score=round(skill_score, 2),
        keyword_score=round(keyword_score, 2),
        availability_score=availability_score,
        matched_skills=[s for s in candidate.skills if s.lower() in job_skills_lower],
        missing_skills=[s for s in job_skills_lower if s not in candidate_skills_lower],
    )


@router.get("/matching/{job_id}", response_model=CandidateMatchResponse)
async def get_ai_candidate_matches(
    job_id: str,
    limit: int = Query(default=10, le=50, description="Number of top-ranked candidates to return"),
    current_user: User = Depends(RoleChecker(["SUPER_ADMIN", "ADMIN", "RECRUITER"]))
) -> Any:
    """
    AI-powered candidate ranking for a job.
    Uses weighted scoring across skills (60%), keywords (25%), and availability (15%).
    Returns ranked candidates sorted by total_score descending.
    """
    job = await Job.get(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    # Extract keywords from job description (non-stop words with len >= 4)
    stop_words = {"with", "that", "this", "from", "will", "have", "been", "their", "they", "your", "what"}
    description_keywords = [
        word.strip(".,()[]").lower()
        for word in job.description.split()
        if len(word) >= 4 and word.lower() not in stop_words
    ]

    all_candidates = await Candidate.find_all().to_list()
    if not all_candidates:
        return CandidateMatchResponse(
            job_id=job_id,
            job_title=job.title,
            total_candidates_evaluated=0,
            ranked_candidates=[]
        )

    scores = [
        _compute_candidate_score(c, job.pipeline_stages[:0] or [], description_keywords)
        for c in all_candidates
    ]
    # Use job description keywords as the proxy for required skills when no explicit list
    job_required_skills = [kw for kw in description_keywords[:15]]  # top 15 keywords as skills proxy
    scores = [
        _compute_candidate_score(c, job_required_skills, description_keywords)
        for c in all_candidates
    ]
    scores.sort(key=lambda x: x.total_score, reverse=True)

    return CandidateMatchResponse(
        job_id=job_id,
        job_title=job.title,
        total_candidates_evaluated=len(all_candidates),
        ranked_candidates=scores[:limit],
    )


# ──────────────────────────────────────────────────────────────────────────────
# 2. SMART HIRING ANALYTICS
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/analytics/hiring", response_model=HiringAnalyticsResponse)
async def get_hiring_analytics(
    current_user: User = Depends(RoleChecker(["SUPER_ADMIN", "ADMIN"]))
) -> Any:
    """
    Platform-wide hiring analytics:
    - Stage distribution & drop-off rates across all applications
    - Per-recruiter job load and application volume
    """
    all_applications = await Application.find_all().to_list()
    all_jobs = await Job.find_all().to_list()
    total_applications = len(all_applications)

    # ── Stage analytics ───────────────────────────────────────────────────────
    stage_counts: dict = {}
    for app in all_applications:
        stage_counts[app.current_stage] = stage_counts.get(app.current_stage, 0) + 1

    stage_analytics = []
    stage_names = list(stage_counts.keys())
    for i, stage in enumerate(stage_names):
        count = stage_counts[stage]
        # Drop-off: % of total that never make it beyond this stage
        remaining_after = sum(stage_counts[s] for s in stage_names[i+1:]) if i + 1 < len(stage_names) else 0
        if count > 0:
            drop_off = round(((count - remaining_after) / count) * 100, 2)
        else:
            drop_off = 0.0
        stage_analytics.append(StageAnalytics(
            stage_name=stage,
            candidate_count=count,
            drop_off_rate=drop_off,
        ))

    # ── Recruiter performance ─────────────────────────────────────────────────
    recruiter_map: dict = {}
    for job in all_jobs:
        if job.recruiter_id:
            if job.recruiter_id not in recruiter_map:
                recruiter_map[job.recruiter_id] = {
                    "total_jobs": 0, "open_jobs": 0, "closed_jobs": 0
                }
            recruiter_map[job.recruiter_id]["total_jobs"] += 1
            if job.status == "OPEN":
                recruiter_map[job.recruiter_id]["open_jobs"] += 1
            else:
                recruiter_map[job.recruiter_id]["closed_jobs"] += 1

    # Count applications per recruiter (via job linkage)
    job_to_recruiter = {str(j.id): j.recruiter_id for j in all_jobs if j.recruiter_id}
    for app in all_applications:
        recruiter_id = job_to_recruiter.get(app.job_id)
        if recruiter_id and recruiter_id in recruiter_map:
            recruiter_map[recruiter_id]["applications"] = recruiter_map[recruiter_id].get("applications", 0) + 1

    recruiter_performance = []
    for rid, stats in recruiter_map.items():
        user = await User.get(rid)
        recruiter_performance.append(RecruiterPerformance(
            recruiter_id=rid,
            recruiter_email=user.email if user else None,
            total_jobs=stats["total_jobs"],
            open_jobs=stats["open_jobs"],
            closed_jobs=stats["closed_jobs"],
            total_applications=stats.get("applications", 0),
        ))

    return HiringAnalyticsResponse(
        total_applications=total_applications,
        total_jobs=len(all_jobs),
        stage_analytics=stage_analytics,
        recruiter_performance=recruiter_performance,
    )


# ──────────────────────────────────────────────────────────────────────────────
# 3. REAL-TIME ACTIVITY FEED
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/activity-feed", response_model=List[ActivityLogResponse])
async def get_activity_feed(
    limit: int = Query(default=50, le=200),
    event_type: Optional[str] = Query(default=None, description="Filter by event type"),
    entity_type: Optional[str] = Query(default=None, description="Filter by entity type"),
    current_user: User = Depends(RoleChecker(["SUPER_ADMIN", "ADMIN"]))
) -> Any:
    """
    Retrieve the latest system-wide activity events, sorted by newest first.
    Supports filtering by event_type and entity_type.
    """
    query: dict = {}
    if event_type:
        query["event_type"] = event_type
    if entity_type:
        query["entity_type"] = entity_type

    return await ActivityLog.find(query).sort("-created_at").limit(limit).to_list()


# ──────────────────────────────────────────────────────────────────────────────
# 4. WORKFLOW AUTOMATION ENGINE - CRUD
# ──────────────────────────────────────────────────────────────────────────────

@router.post("/workflows", response_model=WorkflowRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_workflow_rule(
    rule_in: WorkflowRuleCreate,
    current_user: User = Depends(RoleChecker(["SUPER_ADMIN", "ADMIN"]))
) -> Any:
    """
    Create a new automation rule.
    Example: IF trigger_event="INVOICE_PAID" THEN action_type="SEND_EMAIL"
    """
    rule = WorkflowRule(
        name=rule_in.name,
        description=rule_in.description,
        is_active=rule_in.is_active,
        trigger_event=rule_in.trigger_event,
        conditions=rule_in.conditions,
        action_type=rule_in.action_type,
        action_config=rule_in.action_config,
        created_by=str(current_user.id),
    )
    await rule.insert()
    return rule


@router.get("/workflows", response_model=List[WorkflowRuleResponse])
async def list_workflow_rules(
    active_only: bool = Query(default=False),
    current_user: User = Depends(RoleChecker(["SUPER_ADMIN", "ADMIN"]))
) -> Any:
    """List all automation workflow rules. Filter to only active ones with ?active_only=true."""
    if active_only:
        return await WorkflowRule.find(WorkflowRule.is_active == True).to_list()
    return await WorkflowRule.find_all().to_list()


@router.get("/workflows/{rule_id}", response_model=WorkflowRuleResponse)
async def get_workflow_rule(
    rule_id: str,
    current_user: User = Depends(RoleChecker(["SUPER_ADMIN", "ADMIN"]))
) -> Any:
    """Get a single workflow automation rule by ID."""
    rule = await WorkflowRule.get(rule_id)
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow rule not found")
    return rule


@router.put("/workflows/{rule_id}", response_model=WorkflowRuleResponse)
async def update_workflow_rule(
    rule_id: str,
    rule_in: WorkflowRuleUpdate,
    current_user: User = Depends(RoleChecker(["SUPER_ADMIN", "ADMIN"]))
) -> Any:
    """Update an existing workflow automation rule."""
    rule = await WorkflowRule.get(rule_id)
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow rule not found")

    update_data = rule_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(rule, field, value)
    rule.updated_at = datetime.now(timezone.utc)
    await rule.save()
    return rule


@router.delete("/workflows/{rule_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_workflow_rule(
    rule_id: str,
    current_user: User = Depends(RoleChecker(["SUPER_ADMIN"]))
) -> None:
    """Permanently delete an automation workflow rule. SUPER_ADMIN only."""
    rule = await WorkflowRule.get(rule_id)
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow rule not found")
    await rule.delete()
    return None
