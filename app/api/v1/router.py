from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth, user, company, job, candidate, crm, billing, cms, admin, health, content, upload
)

api_router = APIRouter()

# Register modular sub-routers under appropriate prefixes and Swagger tags
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(user.router, prefix="/users", tags=["Users"])
api_router.include_router(company.router, prefix="/companies", tags=["Companies"])
api_router.include_router(job.router, prefix="/jobs", tags=["Jobs"])
api_router.include_router(candidate.router, prefix="/candidates", tags=["Candidates & Applications"])
api_router.include_router(crm.router, prefix="/crm", tags=["CRM & Leads"])
api_router.include_router(billing.router, prefix="/billing", tags=["Billing & Invoices"])
api_router.include_router(cms.router, prefix="/cms", tags=["CMS Content"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin Control Panel"])
api_router.include_router(health.router, prefix="/health", tags=["System Health"])
# New CMS content endpoints (News, Team, Testimonials, Logos, Enquiries, Caregiver Enquiries)
api_router.include_router(content.router, prefix="/content", tags=["Content Management"])
# Cloudinary image upload
api_router.include_router(upload.router, prefix="/media", tags=["Media Upload"])
