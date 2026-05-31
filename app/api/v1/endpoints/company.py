from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from app.api.deps import get_current_active_user, RoleChecker, PermissionChecker
from app.models.company import Company
from app.models.user import User
from app.schemas.platform import CompanyCreate, CompanyUpdate, CompanyResponse
from app.utils.audit import log_action

router = APIRouter()


@router.post("/", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
async def create_company(
    company_in: CompanyCreate,
    request: Request,
    current_user: User = Depends(PermissionChecker("manage_companies"))
) -> Any:
    """
    Register a new company profile.
    Requires 'manage_companies' permission.
    """
    company = Company(
        name=company_in.name,
        domain=company_in.domain,
        industry=company_in.industry,
        description=company_in.description,
        managers=company_in.managers,
    )
    await company.insert()
    
    await log_action(
        action="CREATE_COMPANY",
        details=f"Created company: {company.name} (id: {company.id})",
        user=current_user,
        request=request
    )
    return company


@router.get("/", response_model=List[CompanyResponse])
async def list_companies(
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Public endpoint to get a paginated list of all registered company profiles.
    """
    return await Company.find_all().skip(skip).limit(limit).to_list()


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company_by_id(
    company_id: str,
) -> Any:
    """
    Public endpoint to retrieve specific company profile by its ID.
    """
    company = await Company.get(company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company profile not found",
        )
    return company


@router.put("/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: str,
    company_in: CompanyUpdate,
    request: Request,
    current_user: User = Depends(PermissionChecker("manage_companies"))
) -> Any:
    """
    Modify an existing company profile.
    Requires 'manage_companies' permission.
    """
    company = await Company.get(company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company profile not found",
        )
        
    update_data = company_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(company, field, value)
        
    await company.save()
    
    await log_action(
        action="UPDATE_COMPANY",
        details=f"Updated company: {company.name} (id: {company.id})",
        user=current_user,
        request=request
    )
    return company


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_company(
    company_id: str,
    request: Request,
    current_user: User = Depends(PermissionChecker("manage_companies"))
) -> None:
    """
    Delete a company profile.
    Requires 'manage_companies' permission.
    """
    company = await Company.get(company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_440_NOT_FOUND,
            detail="Company profile not found",
        )
    company_name = company.name
    await company.delete()
    
    await log_action(
        action="DELETE_COMPANY",
        details=f"Deleted company profile: {company_name} (id: {company_id})",
        user=current_user,
        request=request
    )
    return None
