import asyncio
import logging
from datetime import datetime, timedelta
from app.core.security import get_password_hash
from app.db.mongo import init_db
from app.models.role import Role
from app.models.user import User
from app.models.company import Company
from app.models.job import Job
from app.models.candidate import Candidate
from app.models.application import Application
from app.models.lead import Lead
from app.models.invoice import Invoice
from app.models.cms import CMSPage, CMSBlog, CMSService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed")


async def seed_data():
    logger.info("Initializing Beanie ODM for seeding...")
    await init_db()
    
    # ----------------------------------------------------
    # 1. SEED ROLES & PERMISSIONS
    # ----------------------------------------------------
    logger.info("Seeding system roles...")
    
    roles_definitions = {
        "SUPER_ADMIN": ["*"],
        "ADMIN": [
            "manage_users", 
            "manage_companies", 
            "manage_jobs", 
            "manage_candidates", 
            "manage_crm", 
            "manage_billing", 
            "manage_cms", 
            "view_reports"
        ],
        "RECRUITER": [
            "manage_jobs", 
            "manage_candidates", 
            "view_reports"
        ],
        "CLIENT": [
            "view_reports"
        ]
    }
    
    for role_name, perms in roles_definitions.items():
        existing_role = await Role.find_one(Role.name == role_name)
        if not existing_role:
            role = Role(name=role_name, permissions=perms)
            await role.insert()
            logger.info(f"Created role: {role_name}")
            
    # ----------------------------------------------------
    # 2. SEED DEFAULT SUPER ADMIN
    # ----------------------------------------------------
    logger.info("Checking for default SUPER_ADMIN user...")
    admin_email = "premjeet.dev26@gmail.com"
    admin_user = await User.find_one(User.email == admin_email)
    
    if not admin_user:
        admin_user = User(
            email=admin_email,
            name="CoreVita Administrator",
            hashed_password=get_password_hash("admin123"),
            role="SUPER_ADMIN",
            is_active=True
        )
        await admin_user.insert()
        logger.info(f"Created default SUPER_ADMIN user: {admin_email} (password: adminpassword123)")
    else:
        logger.info("SUPER_ADMIN user already exists.")
        
    # ----------------------------------------------------
    # 3. SEED MOCK COMPANIES
    # ----------------------------------------------------
    logger.info("Seeding mock companies...")
    companies_count = await Company.count()
    if companies_count == 0:
        company_a = Company(
            name="Acme Corporation",
            domain="acme.com",
            industry="Technology",
            description="Leading global SaaS provider specializing in enterprise automation solutions.",
            managers=["recruiter@corevita.co"]
        )
        await company_a.insert()
        
        company_b = Company(
            name="Innovate Financials",
            domain="innovatefin.com",
            industry="Finance",
            description="Innovative boutique asset management and micro-lending consultancy.",
            managers=[]
        )
        await company_b.insert()
        logger.info("Mock companies seeded.")
    else:
        logger.info("Companies already exist, skipping...")
        
    # ----------------------------------------------------
    # 4. SEED MOCK JOBS
    # ----------------------------------------------------
    logger.info("Seeding mock jobs...")
    jobs_count = await Job.count()
    if jobs_count == 0:
        # Fetch seeded companies
        comp_a = await Company.find_one(Company.name == "Acme Corporation")
        comp_b = await Company.find_one(Company.name == "Innovate Financials")
        
        job_1 = Job(
            title="Senior Python Backend Developer",
            description="We are seeking an expert FastAPI developer to architect high-throughput APIs.",
            company_id=str(comp_a.id),
            recruiter_id=str(admin_user.id),
            status="OPEN",
            pipeline_stages=["Screened", "Technical Assessment", "Final Interview", "Offer"],
            salary_range="120,000 - 150,000 USD"
        )
        await job_1.insert()
        
        job_2 = Job(
            title="Financial Risk Quantitative Analyst",
            description="Quantitative analysis role specializing in probabilistic risk engines.",
            company_id=str(comp_b.id),
            status="OPEN",
            pipeline_stages=["Resume Review", "Quantitative Test", "Panel Interview", "Offer"],
            salary_range="140,000 - 180,000 USD"
        )
        await job_2.insert()
        logger.info("Mock jobs seeded.")
    else:
        logger.info("Jobs already exist, skipping...")

    # ----------------------------------------------------
    # 5. SEED MOCK CANDIDATES & APPLICATIONS
    # ----------------------------------------------------
    logger.info("Seeding mock candidates...")
    candidates_count = await Candidate.count()
    if candidates_count == 0:
        c1 = Candidate(
            name="Jane Doe",
            email="jane.doe@gmail.com",
            phone="+1234567890",
            skills=["python", "fastapi", "mongodb", "aws"],
            cv_url="https://s3.amazonaws.com/corevita-cvs/jane_doe_resume.pdf",
            status="AVAILABLE"
        )
        await c1.insert()
        
        c2 = Candidate(
            name="John Smith",
            email="john.smith@yahoo.com",
            phone="+9876543210",
            skills=["quantitative modeling", "statistics", "python"],
            cv_url="https://s3.amazonaws.com/corevita-cvs/john_smith_resume.pdf",
            status="AVAILABLE"
        )
        await c2.insert()
        logger.info("Mock candidates seeded.")
        
        # Seed application
        logger.info("Seeding mock applications...")
        j1 = await Job.find_one(Job.title == "Senior Python Backend Developer")
        app1 = Application(
            job_id=str(j1.id),
            candidate_id=str(c1.id),
            current_stage="Screened",
            notes=["Strong backend foundations, highly motivated."]
        )
        await app1.insert()
        logger.info("Mock applications seeded.")
    else:
        logger.info("Candidates already exist, skipping...")

    # ----------------------------------------------------
    # 6. SEED MOCK CRM LEADS
    # ----------------------------------------------------
    logger.info("Seeding mock CRM leads...")
    leads_count = await Lead.count()
    if leads_count == 0:
        lead_1 = Lead(
            company_name="Stark Industries",
            contact_name="Pepper Potts",
            contact_email="pepper@stark.com",
            contact_phone="+111222333",
            status="NEW"
        )
        await lead_1.insert()
        
        lead_2 = Lead(
            company_name="Wayne Enterprises",
            contact_name="Lucius Fox",
            contact_email="lucius@wayne.com",
            contact_phone="+444555666",
            status="CONTACTED",
            assigned_to=str(admin_user.id)
        )
        await lead_2.insert()
        logger.info("Mock CRM leads seeded.")
    else:
        logger.info("CRM leads already exist, skipping...")

    # ----------------------------------------------------
    # 7. SEED MOCK INVOICES
    # ----------------------------------------------------
    logger.info("Seeding mock invoices...")
    invoices_count = await Invoice.count()
    if invoices_count == 0:
        comp_a = await Company.find_one(Company.name == "Acme Corporation")
        comp_b = await Company.find_one(Company.name == "Innovate Financials")
        
        invoice_1 = Invoice(
            invoice_number="INV-2026-001",
            company_id=str(comp_a.id),
            amount=7500.00,
            status="PAID",
            due_date=datetime.utcnow() - timedelta(days=5)
        )
        await invoice_1.insert()
        
        invoice_2 = Invoice(
            invoice_number="INV-2026-002",
            company_id=str(comp_b.id),
            amount=9800.00,
            status="UNPAID",
            due_date=datetime.utcnow() + timedelta(days=25)
        )
        await invoice_2.insert()
        logger.info("Mock invoices seeded.")
    else:
        logger.info("Invoices already exist, skipping...")

    # ----------------------------------------------------
    # 8. SEED CMS CONTENT
    # ----------------------------------------------------
    logger.info("Seeding mock CMS content...")
    cms_pages_count = await CMSPage.count()
    if cms_pages_count == 0:
        page_about = CMSPage(
            slug="about-us",
            title="About CoreVita Advisory Private Limited",
            content="CoreVita Advisory is a premier workforce enablement partner providing absolute administrative efficiency and top-tier talent consulting."
        )
        await page_about.insert()
        
        blog_post = CMSBlog(
            slug="future-of-work",
            title="The Dynamic Future of Consulting and Gig Platforms",
            content="Detailed analysis of global freelancing trends, platform compliance, and developer lifecycle tracking.",
            author="Executive Committee"
        )
        await blog_post.insert()
        
        service_prog = CMSService(
            name="Executive Workforce Recruitment",
            description="Highly personalized executive-level and deep-tech quant recruitment workflows.",
            price=25000.00
        )
        await service_prog.insert()
        logger.info("Mock CMS content seeded.")
    else:
        logger.info("CMS content already exists, skipping...")

    logger.info("Database seeding process completed successfully!")


if __name__ == "__main__":
    asyncio.run(seed_data())
