from datetime import datetime
from typing import List, Optional, Annotated, Any
from pydantic import BaseModel, Field, EmailStr, BeforeValidator

PyObjectId = Annotated[str, BeforeValidator(str)]
# ==============================================================================
# ROLE SCHEMAS
# ==============================================================================
class RoleCreate(BaseModel):
    name: str = Field(..., description="Unique name of the role (e.g. SUPER_ADMIN, ADMIN)")
    permissions: List[str] = Field(default_factory=list, description="List of granular permissions")

class RoleResponse(BaseModel):
    id: PyObjectId
    name: str
    permissions: List[str]

    class Config:
        from_attributes = True

# ==============================================================================
# COMPANY SCHEMAS
# ==============================================================================
class CompanyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    domain: str = Field(..., description="Corporate email/web domain")
    industry: str = Field(..., description="Industry sector")
    description: Optional[str] = None
    managers: List[str] = Field(default_factory=list, description="User emails assigned as managers")

class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    domain: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None
    managers: Optional[List[str]] = None

class CompanyResponse(BaseModel):
    id: PyObjectId
    name: str
    domain: str
    industry: str
    description: Optional[str]
    managers: List[str]
    created_at: datetime

    class Config:
        from_attributes = True

# ==============================================================================
# JOB SCHEMAS
# ==============================================================================
class JobCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: str
    company_id: Optional[str] = Field(None, description="Optional ID of the company hosting the job")
    recruiter_id: Optional[str] = Field(None, description="Optional ID of the assigned Recruiter")
    status: str = Field("OPEN", description="Job status (OPEN, CLOSED, DRAFT)")
    pipeline_stages: List[str] = Field(
        default_factory=lambda: ["Applied", "Screened", "Interviewing", "Offer", "Rejected", "Hired"]
    )
    salary_range: Optional[str] = None
    location: Optional[str] = None
    industry: Optional[str] = None
    job_type: Optional[str] = None
    experience_level: Optional[str] = None

class JobUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    recruiter_id: Optional[str] = None
    status: Optional[str] = None
    pipeline_stages: Optional[List[str]] = None
    salary_range: Optional[str] = None
    location: Optional[str] = None
    industry: Optional[str] = None
    job_type: Optional[str] = None
    experience_level: Optional[str] = None

class JobResponse(BaseModel):
    id: PyObjectId
    title: str
    description: str
    company_id: Optional[str] = None
    recruiter_id: Optional[str]
    status: str
    pipeline_stages: List[str]
    salary_range: Optional[str]
    location: Optional[str]
    industry: Optional[str]
    job_type: Optional[str]
    experience_level: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

# ==============================================================================
# CANDIDATE SCHEMAS
# ==============================================================================
class CandidateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: Optional[str] = None
    skills: List[str] = Field(default_factory=list, description="Candidate core skills")
    cv_url: Optional[str] = Field(None, description="S3 or Cloudinary storage URL")
    status: str = Field("AVAILABLE", description="AVAILABLE, PLACED, INACTIVE")

class CandidateUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    skills: Optional[List[str]] = None
    cv_url: Optional[str] = None
    status: Optional[str] = None

class CandidateResponse(BaseModel):
    id: PyObjectId
    name: str
    email: EmailStr
    phone: Optional[str]
    skills: List[str]
    cv_url: Optional[str]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

# ==============================================================================
# APPLICATION SCHEMAS
# ==============================================================================
class ApplicationCreate(BaseModel):
    job_id: PyObjectId
    candidate_id: PyObjectId
    current_stage: str = "Applied"
    notes: List[str] = Field(default_factory=list)

class PublicApplicationCreate(BaseModel):
    job_id: str = Field(..., description="ID of the job being applied for")
    name: str = Field(..., description="Candidate's full name")
    email: EmailStr = Field(..., description="Candidate's email address")
    phone: str = Field(..., description="Candidate's phone number")
    skills: List[str] = Field(default_factory=list, description="Candidate's core skills")
    cv_url: str = Field(..., description="URL of the uploaded CV/Resume")

class ApplicationUpdate(BaseModel):
    current_stage: str
    notes: Optional[List[str]] = None

class ApplicationResponse(BaseModel):
    id: PyObjectId
    job_id: PyObjectId
    candidate_id: PyObjectId
    current_stage: str
    notes: List[str]
    created_at: datetime

    class Config:
        from_attributes = True

# ==============================================================================
# CRM / LEADS SCHEMAS
# ==============================================================================
class LeadCreate(BaseModel):
    company_name: str
    contact_name: str
    contact_email: EmailStr
    contact_phone: Optional[str] = None
    status: str = Field("NEW", description="NEW, CONTACTED, QUALIFIED, LOST")
    assigned_to: Optional[str] = Field(None, description="Assigned User ID")

class LeadUpdate(BaseModel):
    status: Optional[str] = None
    assigned_to: Optional[str] = None

class LeadResponse(BaseModel):
    id: PyObjectId
    company_name: str
    contact_name: str
    contact_email: EmailStr
    contact_phone: Optional[str]
    status: str
    assigned_to: Optional[str]
    score: int = 0
    last_activity_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

# ==============================================================================
# BILLING / INVOICES / PAYMENTS
# ==============================================================================
class InvoiceCreate(BaseModel):
    invoice_number: str
    company_id: PyObjectId
    amount: float
    due_date: datetime

class InvoiceResponse(BaseModel):
    id: PyObjectId
    invoice_number: str
    company_id: PyObjectId
    amount: float
    status: str
    due_date: datetime
    created_at: datetime

    class Config:
        from_attributes = True

class PaymentCreate(BaseModel):
    invoice_id: PyObjectId
    amount: float
    payment_method: str = "STRIPE"
    transaction_id: Optional[str] = None

class PaymentResponse(BaseModel):
    id: PyObjectId
    invoice_id: PyObjectId
    amount: float
    payment_method: str
    transaction_id: Optional[str]
    status: str
    paid_at: datetime

    class Config:
        from_attributes = True

# ==============================================================================
# CMS SCHEMAS
# ==============================================================================
class CMSPageCreate(BaseModel):
    slug: str
    title: str
    content: str

class CMSPageResponse(BaseModel):
    id: PyObjectId
    slug: str
    title: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True

class CMSBlogCreate(BaseModel):
    slug: str
    title: str
    content: str
    author: str

class CMSBlogResponse(BaseModel):
    id: PyObjectId
    slug: str
    title: str
    content: str
    author: str
    created_at: datetime

    class Config:
        from_attributes = True

class CMSServiceCreate(BaseModel):
    name: str
    description: str
    price: Optional[float] = None

class CMSServiceResponse(BaseModel):
    id: PyObjectId
    name: str
    description: str
    price: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True

# ==============================================================================
# AUDIT LOGS & NOTIFICATIONS
# ==============================================================================
class AuditLogResponse(BaseModel):
    id: PyObjectId
    user_id: Optional[str]
    user_email: Optional[str]
    action: str
    details: str
    ip_address: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class NotificationResponse(BaseModel):
    id: PyObjectId
    recipient_email: EmailStr
    title: str
    message: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

# ==============================================================================
# DASHBOARD / REPORTS
# ==============================================================================
class DashboardKPIs(BaseModel):
    total_users: int
    total_jobs: int
    total_revenue: float
    total_leads: int
    new_leads_count: int
    open_jobs_count: int


# ==============================================================================
# WORKFLOW AUTOMATION ENGINE SCHEMAS
# ==============================================================================
class WorkflowRuleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    is_active: bool = True
    trigger_event: str = Field(..., description="CANDIDATE_STAGE_CHANGED | NEW_LEAD | INVOICE_PAID | APPLICATION_CREATED")
    conditions: dict = Field(default_factory=dict, description="Key-value pairs matched against event payload")
    action_type: str = Field(..., description="SEND_EMAIL | CREATE_ACTIVITY_LOG | UPDATE_LEAD_SCORE")
    action_config: dict = Field(default_factory=dict)

class WorkflowRuleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    conditions: Optional[dict] = None
    action_type: Optional[str] = None
    action_config: Optional[dict] = None

class WorkflowRuleResponse(BaseModel):
    id: PyObjectId
    name: str
    description: Optional[str]
    is_active: bool
    trigger_event: str
    conditions: dict
    action_type: str
    action_config: dict
    trigger_count: int
    last_triggered_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


# ==============================================================================
# ACTIVITY FEED SCHEMAS
# ==============================================================================
class ActivityLogResponse(BaseModel):
    id: PyObjectId
    event_type: str
    entity_type: str
    entity_id: Optional[str]
    title: str
    description: str
    actor_id: Optional[str]
    actor_email: Optional[str]
    metadata: dict
    created_at: datetime

    class Config:
        from_attributes = True


# ==============================================================================
# CANDIDATE TIMELINE SCHEMAS
# ==============================================================================
class CandidateTimelineResponse(BaseModel):
    id: PyObjectId
    candidate_id: str
    event_type: str
    title: str
    description: str
    actor_id: Optional[str]
    actor_email: Optional[str]
    related_job_id: Optional[str]
    related_application_id: Optional[str]
    metadata: dict
    created_at: datetime

    class Config:
        from_attributes = True


# ==============================================================================
# AI CANDIDATE MATCHING SCHEMAS
# ==============================================================================
class CandidateMatchScore(BaseModel):
    candidate_id: str
    candidate_name: str
    candidate_email: str
    skills: List[str]
    status: str
    total_score: float = Field(..., description="Weighted match score 0-100")
    skill_score: float
    keyword_score: float
    availability_score: float
    matched_skills: List[str]
    missing_skills: List[str]

class CandidateMatchResponse(BaseModel):
    job_id: str
    job_title: str
    total_candidates_evaluated: int
    ranked_candidates: List[CandidateMatchScore]


# ==============================================================================
# HIRING ANALYTICS SCHEMAS
# ==============================================================================
class StageAnalytics(BaseModel):
    stage_name: str
    candidate_count: int
    drop_off_rate: float = Field(..., description="Percentage that do not advance past this stage")

class RecruiterPerformance(BaseModel):
    recruiter_id: str
    recruiter_email: Optional[str]
    total_jobs: int
    open_jobs: int
    closed_jobs: int
    total_applications: int

class HiringAnalyticsResponse(BaseModel):
    total_applications: int
    total_jobs: int
    stage_analytics: List[StageAnalytics]
    recruiter_performance: List[RecruiterPerformance]
