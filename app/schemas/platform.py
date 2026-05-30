from datetime import datetime
from typing import List, Optional, Annotated, Any
from pydantic import BaseModel, Field, EmailStr, BeforeValidator

# Custom validator to convert BSON ObjectId/PydanticObjectId to string during serialization
ObjectIdStr = Annotated[str, BeforeValidator(lambda v: str(v) if v is not None else v)]

# ==============================================================================
# ROLE SCHEMAS
# ==============================================================================
class RoleCreate(BaseModel):
    name: str = Field(..., description="Unique name of the role (e.g. SUPER_ADMIN, ADMIN)")
    permissions: List[str] = Field(default_factory=list, description="List of granular permissions")

class RoleResponse(BaseModel):
    id: ObjectIdStr
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
    id: ObjectIdStr
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
    company_id: str = Field(..., description="ID of the company hosting the job")
    recruiter_id: Optional[str] = Field(None, description="Optional ID of the assigned Recruiter")
    status: str = Field("OPEN", description="Job status (OPEN, CLOSED, DRAFT)")
    pipeline_stages: List[str] = Field(
        default_factory=lambda: ["Applied", "Screened", "Interviewing", "Offer", "Rejected", "Hired"]
    )
    salary_range: Optional[str] = None

class JobUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    recruiter_id: Optional[str] = None
    status: Optional[str] = None
    pipeline_stages: Optional[List[str]] = None
    salary_range: Optional[str] = None

class JobResponse(BaseModel):
    id: ObjectIdStr
    title: str
    description: str
    company_id: str
    recruiter_id: Optional[str]
    status: str
    pipeline_stages: List[str]
    salary_range: Optional[str]
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
    id: ObjectIdStr
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
    job_id: str
    candidate_id: str
    current_stage: str = "Applied"
    notes: List[str] = Field(default_factory=list)

class ApplicationUpdate(BaseModel):
    current_stage: str
    notes: Optional[List[str]] = None

class ApplicationResponse(BaseModel):
    id: ObjectIdStr
    job_id: str
    candidate_id: str
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
    id: ObjectIdStr
    company_name: str
    contact_name: str
    contact_email: EmailStr
    contact_phone: Optional[str]
    status: str
    assigned_to: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

# ==============================================================================
# BILLING / INVOICES / PAYMENTS
# ==============================================================================
class InvoiceCreate(BaseModel):
    invoice_number: str
    company_id: str
    amount: float
    due_date: datetime

class InvoiceResponse(BaseModel):
    id: ObjectIdStr
    invoice_number: str
    company_id: str
    amount: float
    status: str
    due_date: datetime
    created_at: datetime

    class Config:
        from_attributes = True

class PaymentCreate(BaseModel):
    invoice_id: str
    amount: float
    payment_method: str = "STRIPE"
    transaction_id: Optional[str] = None

class PaymentResponse(BaseModel):
    id: ObjectIdStr
    invoice_id: str
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
    id: ObjectIdStr
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
    id: ObjectIdStr
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
    id: ObjectIdStr
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
    id: ObjectIdStr
    user_id: Optional[str]
    user_email: Optional[str]
    action: str
    details: str
    ip_address: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class NotificationResponse(BaseModel):
    id: ObjectIdStr
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
