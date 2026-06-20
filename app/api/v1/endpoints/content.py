"""
Content Management API Endpoints
==================================
Full CRUD for: News, Team Members, Testimonials, Client Logos,
Enquiries, and Caregiver Enquiries.

Public GET routes (no auth required):
  GET /content/news                   - List published news
  GET /content/news/{slug}            - Get single news article
  GET /content/team                   - List active team members
  GET /content/testimonials           - List active testimonials
  GET /content/logos                  - List active client logos
  GET /content/jobs                   - Public jobs listing (alias)

Admin routes (auth required):
  POST/PUT/DELETE /content/news/*
  POST/PUT/DELETE /content/team/*
  POST/PUT/DELETE /content/testimonials/*
  POST/PUT/DELETE /content/logos/*
  GET /content/enquiries
  PUT /content/enquiries/{id}
  DELETE /content/enquiries/{id}
  GET /content/caregiver-enquiries
  PUT /content/caregiver-enquiries/{id}
  DELETE /content/caregiver-enquiries/{id}

Public POST (no auth):
  POST /content/enquiries             - Submit a contact enquiry
  POST /content/caregiver-enquiries   - Submit a caregiver request
"""

import csv
import io
from datetime import datetime, timezone
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, EmailStr, Field

from app.api.deps import RoleChecker, PermissionChecker
from app.models.news import News
from app.models.team_member import TeamMember
from app.models.testimonial import Testimonial
from app.models.client_logo import ClientLogo
from app.models.enquiry import Enquiry
from app.models.caregiver_enquiry import CaregiverEnquiry
from app.models.user import User

router = APIRouter()


# ==============================================================================
# PYDANTIC SCHEMAS (inline for self-contained endpoint file)
# ==============================================================================

class NewsCreate(BaseModel):
    slug: str
    title: str
    content: str
    excerpt: Optional[str] = None
    author: str = "CoreVita Admin"
    featured_image_url: Optional[str] = None
    category: Optional[str] = None
    tags: List[str] = []
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    is_published: bool = False
    is_featured: bool = False

class NewsUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    excerpt: Optional[str] = None
    author: Optional[str] = None
    featured_image_url: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    is_published: Optional[bool] = None
    is_featured: Optional[bool] = None

class TeamMemberCreate(BaseModel):
    name: str
    designation: str
    bio: Optional[str] = None
    photo_url: Optional[str] = None
    email: Optional[str] = None
    linkedin_url: Optional[str] = None
    twitter_url: Optional[str] = None
    display_order: int = 0
    is_active: bool = True

class TeamMemberUpdate(BaseModel):
    name: Optional[str] = None
    designation: Optional[str] = None
    bio: Optional[str] = None
    photo_url: Optional[str] = None
    email: Optional[str] = None
    linkedin_url: Optional[str] = None
    twitter_url: Optional[str] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None

class TestimonialCreate(BaseModel):
    client_name: str
    client_designation: Optional[str] = None
    client_company: Optional[str] = None
    client_photo_url: Optional[str] = None
    content: str
    rating: int = Field(default=5, ge=1, le=5)
    is_featured: bool = False
    is_active: bool = True
    display_order: int = 0

class TestimonialUpdate(BaseModel):
    client_name: Optional[str] = None
    client_designation: Optional[str] = None
    client_company: Optional[str] = None
    client_photo_url: Optional[str] = None
    content: Optional[str] = None
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    is_featured: Optional[bool] = None
    is_active: Optional[bool] = None
    display_order: Optional[int] = None

class ClientLogoCreate(BaseModel):
    name: str
    logo_url: str
    website_url: Optional[str] = None
    display_order: int = 0
    is_active: bool = True

class ClientLogoUpdate(BaseModel):
    name: Optional[str] = None
    logo_url: Optional[str] = None
    website_url: Optional[str] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None

class EnquiryCreate(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    company: Optional[str] = None
    service_interest: Optional[str] = None
    message: str

class EnquiryUpdate(BaseModel):
    status: Optional[str] = None
    admin_notes: Optional[List[str]] = None

class CaregiverEnquiryCreate(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    location: Optional[str] = None
    service_type: Optional[str] = None
    care_recipient: Optional[str] = None
    message: str

class CaregiverEnquiryUpdate(BaseModel):
    status: Optional[str] = None
    admin_notes: Optional[List[str]] = None


# ==============================================================================
# NEWS
# ==============================================================================

@router.get("/news", tags=["Content - News"])
async def list_published_news(
    skip: int = 0,
    limit: int = 20,
    category: Optional[str] = None,
    featured_only: bool = False,
) -> Any:
    """Public: list published news articles."""
    query: dict = {"is_published": True}
    if category:
        query["category"] = category
    if featured_only:
        query["is_featured"] = True
    return await News.find(query).sort("-published_at").skip(skip).limit(limit).to_list()


@router.get("/news/all", tags=["Content - News"])
async def list_all_news(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(RoleChecker(["SUPER_ADMIN", "ADMIN", "EDITOR"])),
) -> Any:
    """Admin: list all news (published + drafts)."""
    return await News.find_all().sort("-created_at").skip(skip).limit(limit).to_list()


@router.get("/news/{slug}", tags=["Content - News"])
async def get_news_by_slug(slug: str) -> Any:
    """Public: get a single news article by slug."""
    article = await News.find_one(News.slug == slug)
    if not article:
        raise HTTPException(status_code=404, detail="News article not found.")
    return article


@router.post("/news", status_code=status.HTTP_201_CREATED, tags=["Content - News"])
async def create_news(
    data: NewsCreate,
    current_user: User = Depends(RoleChecker(["SUPER_ADMIN", "ADMIN", "EDITOR"])),
) -> Any:
    """Admin: create a news article."""
    existing = await News.find_one(News.slug == data.slug)
    if existing:
        raise HTTPException(status_code=400, detail=f"News with slug '{data.slug}' already exists.")
    article = News(**data.model_dump())
    if data.is_published:
        article.published_at = datetime.now(timezone.utc)
    await article.insert()
    return article


@router.put("/news/{article_id}", tags=["Content - News"])
async def update_news(
    article_id: str,
    data: NewsUpdate,
    current_user: User = Depends(RoleChecker(["SUPER_ADMIN", "ADMIN", "EDITOR"])),
) -> Any:
    """Admin: update a news article."""
    article = await News.get(article_id)
    if not article:
        raise HTTPException(status_code=404, detail="News article not found.")
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(article, field, value)
    if "is_published" in update_data and update_data["is_published"] and not article.published_at:
        article.published_at = datetime.now(timezone.utc)
    article.updated_at = datetime.now(timezone.utc)
    await article.save()
    return article


@router.delete("/news/{article_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response, tags=["Content - News"])
async def delete_news(
    article_id: str,
    current_user: User = Depends(RoleChecker(["SUPER_ADMIN", "ADMIN"])),
) -> None:
    """Admin: delete a news article."""
    article = await News.get(article_id)
    if not article:
        raise HTTPException(status_code=404, detail="News article not found.")
    await article.delete()


# ==============================================================================
# TEAM MEMBERS
# ==============================================================================

@router.get("/team", tags=["Content - Team"])
async def list_team_members(active_only: bool = True) -> Any:
    """Public: list team members."""
    if active_only:
        return await TeamMember.find(TeamMember.is_active == True).sort("display_order").to_list()
    return await TeamMember.find_all().sort("display_order").to_list()


@router.post("/team", status_code=status.HTTP_201_CREATED, tags=["Content - Team"])
async def create_team_member(
    data: TeamMemberCreate,
    current_user: User = Depends(RoleChecker(["SUPER_ADMIN", "ADMIN"])),
) -> Any:
    """Admin: add a team member."""
    member = TeamMember(**data.model_dump())
    await member.insert()
    return member


@router.put("/team/{member_id}", tags=["Content - Team"])
async def update_team_member(
    member_id: str,
    data: TeamMemberUpdate,
    current_user: User = Depends(RoleChecker(["SUPER_ADMIN", "ADMIN"])),
) -> Any:
    """Admin: update a team member."""
    member = await TeamMember.get(member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Team member not found.")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(member, field, value)
    member.updated_at = datetime.now(timezone.utc)
    await member.save()
    return member


@router.delete("/team/{member_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response, tags=["Content - Team"])
async def delete_team_member(
    member_id: str,
    current_user: User = Depends(RoleChecker(["SUPER_ADMIN", "ADMIN"])),
) -> None:
    """Admin: delete a team member."""
    member = await TeamMember.get(member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Team member not found.")
    await member.delete()


# ==============================================================================
# TESTIMONIALS
# ==============================================================================

@router.get("/testimonials", tags=["Content - Testimonials"])
async def list_testimonials(featured_only: bool = False) -> Any:
    """Public: list active testimonials."""
    query: dict = {"is_active": True}
    if featured_only:
        query["is_featured"] = True
    return await Testimonial.find(query).sort("display_order").to_list()


@router.get("/testimonials/all", tags=["Content - Testimonials"])
async def list_all_testimonials(
    current_user: User = Depends(RoleChecker(["SUPER_ADMIN", "ADMIN"])),
) -> Any:
    """Admin: list all testimonials."""
    return await Testimonial.find_all().sort("-created_at").to_list()


@router.post("/testimonials", status_code=status.HTTP_201_CREATED, tags=["Content - Testimonials"])
async def create_testimonial(
    data: TestimonialCreate,
    current_user: User = Depends(RoleChecker(["SUPER_ADMIN", "ADMIN"])),
) -> Any:
    """Admin: add a testimonial."""
    t = Testimonial(**data.model_dump())
    await t.insert()
    return t


@router.put("/testimonials/{testimonial_id}", tags=["Content - Testimonials"])
async def update_testimonial(
    testimonial_id: str,
    data: TestimonialUpdate,
    current_user: User = Depends(RoleChecker(["SUPER_ADMIN", "ADMIN"])),
) -> Any:
    """Admin: update a testimonial."""
    t = await Testimonial.get(testimonial_id)
    if not t:
        raise HTTPException(status_code=404, detail="Testimonial not found.")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(t, field, value)
    t.updated_at = datetime.now(timezone.utc)
    await t.save()
    return t


@router.delete("/testimonials/{testimonial_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response, tags=["Content - Testimonials"])
async def delete_testimonial(
    testimonial_id: str,
    current_user: User = Depends(RoleChecker(["SUPER_ADMIN", "ADMIN"])),
) -> None:
    """Admin: delete a testimonial."""
    t = await Testimonial.get(testimonial_id)
    if not t:
        raise HTTPException(status_code=404, detail="Testimonial not found.")
    await t.delete()


# ==============================================================================
# CLIENT LOGOS
# ==============================================================================

@router.get("/logos", tags=["Content - Logos"])
async def list_client_logos(active_only: bool = True) -> Any:
    """Public: list client logos."""
    if active_only:
        return await ClientLogo.find(ClientLogo.is_active == True).sort("display_order").to_list()
    return await ClientLogo.find_all().sort("display_order").to_list()


@router.post("/logos", status_code=status.HTTP_201_CREATED, tags=["Content - Logos"])
async def create_client_logo(
    data: ClientLogoCreate,
    current_user: User = Depends(RoleChecker(["SUPER_ADMIN", "ADMIN"])),
) -> Any:
    """Admin: add a client logo."""
    logo = ClientLogo(**data.model_dump())
    await logo.insert()
    return logo


@router.put("/logos/{logo_id}", tags=["Content - Logos"])
async def update_client_logo(
    logo_id: str,
    data: ClientLogoUpdate,
    current_user: User = Depends(RoleChecker(["SUPER_ADMIN", "ADMIN"])),
) -> Any:
    """Admin: update a client logo."""
    logo = await ClientLogo.get(logo_id)
    if not logo:
        raise HTTPException(status_code=404, detail="Client logo not found.")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(logo, field, value)
    logo.updated_at = datetime.now(timezone.utc)
    await logo.save()
    return logo


@router.delete("/logos/{logo_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response, tags=["Content - Logos"])
async def delete_client_logo(
    logo_id: str,
    current_user: User = Depends(RoleChecker(["SUPER_ADMIN", "ADMIN"])),
) -> None:
    """Admin: delete a client logo."""
    logo = await ClientLogo.get(logo_id)
    if not logo:
        raise HTTPException(status_code=404, detail="Client logo not found.")
    await logo.delete()


# ==============================================================================
# ENQUIRIES
# ==============================================================================

@router.post("/enquiries", status_code=status.HTTP_201_CREATED, tags=["Content - Enquiries"])
async def submit_enquiry(data: EnquiryCreate) -> Any:
    """Public: submit a general contact enquiry."""
    enquiry = Enquiry(**data.model_dump())
    await enquiry.insert()
    return {"message": "Your enquiry has been submitted. Our team will be in touch soon!", "id": str(enquiry.id)}


@router.get("/enquiries", tags=["Content - Enquiries"])
async def list_enquiries(
    skip: int = 0,
    limit: int = 50,
    status_filter: Optional[str] = Query(default=None, alias="status"),
    search: Optional[str] = None,
    current_user: User = Depends(RoleChecker(["SUPER_ADMIN", "ADMIN"])),
) -> Any:
    """Admin: list all enquiries with filter/search."""
    query: dict = {}
    if status_filter:
        query["status"] = status_filter
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}},
            {"company": {"$regex": search, "$options": "i"}},
        ]
    return await Enquiry.find(query).sort("-created_at").skip(skip).limit(limit).to_list()


@router.put("/enquiries/{enquiry_id}", tags=["Content - Enquiries"])
async def update_enquiry(
    enquiry_id: str,
    data: EnquiryUpdate,
    current_user: User = Depends(RoleChecker(["SUPER_ADMIN", "ADMIN"])),
) -> Any:
    """Admin: update enquiry status or add notes."""
    enquiry = await Enquiry.get(enquiry_id)
    if not enquiry:
        raise HTTPException(status_code=404, detail="Enquiry not found.")
    if data.status:
        enquiry.status = data.status
    if data.admin_notes:
        enquiry.admin_notes.extend(data.admin_notes)
    enquiry.updated_at = datetime.now(timezone.utc)
    await enquiry.save()
    return enquiry


@router.delete("/enquiries/{enquiry_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response, tags=["Content - Enquiries"])
async def delete_enquiry(
    enquiry_id: str,
    current_user: User = Depends(RoleChecker(["SUPER_ADMIN", "ADMIN"])),
) -> None:
    """Admin: delete an enquiry record."""
    enquiry = await Enquiry.get(enquiry_id)
    if not enquiry:
        raise HTTPException(status_code=404, detail="Enquiry not found.")
    await enquiry.delete()


@router.get("/enquiries/export-csv", tags=["Content - Enquiries"])
async def export_enquiries_csv(
    current_user: User = Depends(RoleChecker(["SUPER_ADMIN", "ADMIN"])),
) -> StreamingResponse:
    """Admin: export all enquiries as CSV."""
    enquiries = await Enquiry.find_all().sort("-created_at").to_list()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Name", "Email", "Phone", "Company", "Service Interest", "Message", "Status", "Created At"])
    for e in enquiries:
        writer.writerow([str(e.id), e.name, e.email, e.phone or "", e.company or "", e.service_interest or "", e.message, e.status, e.created_at.strftime("%Y-%m-%d %H:%M")])
    output.seek(0)
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=enquiries.csv"})


# ==============================================================================
# CAREGIVER ENQUIRIES
# ==============================================================================

@router.post("/caregiver-enquiries", status_code=status.HTTP_201_CREATED, tags=["Content - Caregiver"])
async def submit_caregiver_enquiry(data: CaregiverEnquiryCreate) -> Any:
    """Public: submit a caregiver staffing request."""
    enquiry = CaregiverEnquiry(**data.model_dump())
    await enquiry.insert()
    return {"message": "Your caregiver request has been received. We will contact you shortly!", "id": str(enquiry.id)}


@router.get("/caregiver-enquiries", tags=["Content - Caregiver"])
async def list_caregiver_enquiries(
    skip: int = 0,
    limit: int = 50,
    status_filter: Optional[str] = Query(default=None, alias="status"),
    search: Optional[str] = None,
    current_user: User = Depends(RoleChecker(["SUPER_ADMIN", "ADMIN"])),
) -> Any:
    """Admin: list all caregiver enquiries."""
    query: dict = {}
    if status_filter:
        query["status"] = status_filter
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}},
            {"location": {"$regex": search, "$options": "i"}},
        ]
    return await CaregiverEnquiry.find(query).sort("-created_at").skip(skip).limit(limit).to_list()


@router.put("/caregiver-enquiries/{enquiry_id}", tags=["Content - Caregiver"])
async def update_caregiver_enquiry(
    enquiry_id: str,
    data: CaregiverEnquiryUpdate,
    current_user: User = Depends(RoleChecker(["SUPER_ADMIN", "ADMIN"])),
) -> Any:
    """Admin: update caregiver enquiry status or add notes."""
    enquiry = await CaregiverEnquiry.get(enquiry_id)
    if not enquiry:
        raise HTTPException(status_code=404, detail="Caregiver enquiry not found.")
    if data.status:
        enquiry.status = data.status
    if data.admin_notes:
        enquiry.admin_notes.extend(data.admin_notes)
    enquiry.updated_at = datetime.now(timezone.utc)
    await enquiry.save()
    return enquiry


@router.delete("/caregiver-enquiries/{enquiry_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response, tags=["Content - Caregiver"])
async def delete_caregiver_enquiry(
    enquiry_id: str,
    current_user: User = Depends(RoleChecker(["SUPER_ADMIN", "ADMIN"])),
) -> None:
    """Admin: delete a caregiver enquiry."""
    enquiry = await CaregiverEnquiry.get(enquiry_id)
    if not enquiry:
        raise HTTPException(status_code=404, detail="Caregiver enquiry not found.")
    await enquiry.delete()


@router.get("/caregiver-enquiries/export-csv", tags=["Content - Caregiver"])
async def export_caregiver_enquiries_csv(
    current_user: User = Depends(RoleChecker(["SUPER_ADMIN", "ADMIN"])),
) -> StreamingResponse:
    """Admin: export all caregiver enquiries as CSV."""
    enquiries = await CaregiverEnquiry.find_all().sort("-created_at").to_list()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Name", "Email", "Phone", "Location", "Service Type", "Care Recipient", "Message", "Status", "Created At"])
    for e in enquiries:
        writer.writerow([str(e.id), e.name, e.email, e.phone or "", e.location or "", e.service_type or "", e.care_recipient or "", e.message, e.status, e.created_at.strftime("%Y-%m-%d %H:%M")])
    output.seek(0)
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=caregiver_enquiries.csv"})
