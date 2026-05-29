from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from app.api.deps import get_current_active_user, RoleChecker, PermissionChecker
from app.models.lead import Lead
from app.models.user import User
from app.schemas.platform import LeadCreate, LeadUpdate, LeadResponse
from app.utils.audit import log_action

router = APIRouter()


@router.post("/", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
async def create_lead(
    lead_in: LeadCreate,
    request: Request,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Submit or register a new client sales lead.
    Open to any logged-in user.
    """
    if lead_in.assigned_to:
        assignee = await User.get(lead_in.assigned_to)
        if not assignee:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Assigned user ID {lead_in.assigned_to} does not exist."
            )

    lead = Lead(
        company_name=lead_in.company_name,
        contact_name=lead_in.contact_name,
        contact_email=lead_in.contact_email,
        contact_phone=lead_in.contact_phone,
        status=lead_in.status,
        assigned_to=lead_in.assigned_to,
    )
    await lead.insert()
    
    await log_action(
        action="CREATE_LEAD",
        details=f"Created CRM Lead for company: {lead.company_name}",
        user=current_user,
        request=request
    )
    return lead


@router.get("/", response_model=List[LeadResponse])
async def list_leads(
    skip: int = 0,
    limit: int = 100,
    status_filter: str = None,
    current_user: User = Depends(RoleChecker(["SUPER_ADMIN", "ADMIN", "RECRUITER"]))
) -> Any:
    """
    List registered CRM Leads. Supports filtering by status (NEW, CONTACTED, etc.).
    Accessible to admins and recruiters.
    """
    query = {}
    if status_filter:
        query["status"] = status_filter
        
    return await Lead.find(query).skip(skip).limit(limit).to_list()


@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead_by_id(
    lead_id: str,
    current_user: User = Depends(RoleChecker(["SUPER_ADMIN", "ADMIN", "RECRUITER"]))
) -> Any:
    """
    Fetch specific CRM lead by ID.
    """
    lead = await Lead.get(lead_id)
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found",
        )
    return lead


@router.put("/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: str,
    lead_in: LeadUpdate,
    request: Request,
    current_user: User = Depends(PermissionChecker("manage_crm"))
) -> Any:
    """
    Update lead assignment or status.
    Requires 'manage_crm' permission.
    """
    lead = await Lead.get(lead_id)
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found",
        )
        
    if lead_in.assigned_to:
        assignee = await User.get(lead_in.assigned_to)
        if not assignee:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Assigned user ID {lead_in.assigned_to} does not exist."
            )

    update_data = lead_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(lead, field, value)
        
    await lead.save()
    
    await log_action(
        action="UPDATE_LEAD",
        details=f"Updated lead: {lead.company_name} (Status: {lead.status}, Assigned: {lead.assigned_to})",
        user=current_user,
        request=request
    )
    return lead


@router.delete("/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lead(
    lead_id: str,
    request: Request,
    current_user: User = Depends(PermissionChecker("manage_crm"))
) -> Any:
    """
    Delete a CRM Lead.
    Requires 'manage_crm' permission.
    """
    lead = await Lead.get(lead_id)
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found",
        )
    comp = lead.company_name
    await lead.delete()
    
    await log_action(
        action="DELETE_LEAD",
        details=f"Deleted CRM lead for: {comp} (id: {lead_id})",
        user=current_user,
        request=request
    )
    return None
