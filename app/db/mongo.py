from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

# Import all Beanie documents
from app.models.role import Role
from app.models.user import User
from app.models.company import Company
from app.models.job import Job
from app.models.candidate import Candidate
from app.models.application import Application
from app.models.lead import Lead
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.audit_log import AuditLog
from app.models.notification import Notification
from app.models.cms import CMSPage, CMSBlog, CMSService
# New intelligence models
from app.models.activity_log import ActivityLog
from app.models.workflow import WorkflowRule
from app.models.candidate_timeline import CandidateTimeline

# Instantiate global Motor Client
client = AsyncIOMotorClient(settings.MONGODB_URL)
db = client[settings.MONGODB_DB_NAME]

async def init_db():
    """
    Initialize Beanie ODM with the active MongoDB database and document models.
    """
    await init_beanie(
        database=db,
        document_models=[
            Role,
            User,
            Company,
            Job,
            Candidate,
            Application,
            Lead,
            Invoice,
            Payment,
            AuditLog,
            Notification,
            CMSPage,
            CMSBlog,
            CMSService,
            # New intelligence collections
            ActivityLog,
            WorkflowRule,
            CandidateTimeline,
        ]
    )
