from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from app.api.deps import get_current_active_user, RoleChecker, PermissionChecker
from app.models.job import Job
from app.models.company import Company
from app.models.user import User
from app.schemas.platform import JobCreate, JobUpdate, JobResponse
from app.utils.audit import log_action

router = APIRouter()


@router.post("/", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    job_in: JobCreate,
    request: Request,
    current_user: User = Depends(PermissionChecker("manage_jobs"))
) -> Any:
    """
    Create a new job listing for a company.
    Requires 'manage_jobs' permission.
    """
    # Verify company exists
    company = await Company.get(job_in.company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Company with ID {job_in.company_id} does not exist."
        )
        
    # Verify recruiter exists if provided
    if job_in.recruiter_id:
        recruiter = await User.get(job_in.recruiter_id)
        if not recruiter:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Recruiter user with ID {job_in.recruiter_id} does not exist."
            )

    job = Job(
        title=job_in.title,
        description=job_in.description,
        company_id=job_in.company_id,
        recruiter_id=job_in.recruiter_id,
        status=job_in.status,
        pipeline_stages=job_in.pipeline_stages,
        salary_range=job_in.salary_range,
    )
    await job.insert()
    
    await log_action(
        action="CREATE_JOB",
        details=f"Created job listing: {job.title} for {company.name}",
        user=current_user,
        request=request
    )
    return job


@router.get("/", response_model=List[JobResponse])
async def list_jobs(
    skip: int = 0,
    limit: int = 100,
    status_filter: str = None,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Fetch a paginated list of jobs. Can filter by status (e.g. OPEN, CLOSED).
    """
    query = {}
    if status_filter:
        query["status"] = status_filter
        
    return await Job.find(query).skip(skip).limit(limit).to_list()


@router.get("/{job_id}", response_model=JobResponse)
async def get_job_by_id(
    job_id: str,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Retrieve specific job profile details by ID.
    """
    job = await Job.get(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job listing not found",
        )
    return job


@router.put("/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: str,
    job_in: JobUpdate,
    request: Request,
    current_user: User = Depends(PermissionChecker("manage_jobs"))
) -> Any:
    """
    Update job description, status, pipeline stages, or recruiters.
    Requires 'manage_jobs' permission.
    """
    job = await Job.get(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job listing not found",
        )
        
    if job_in.recruiter_id:
        recruiter = await User.get(job_in.recruiter_id)
        if not recruiter:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Recruiter user with ID {job_in.recruiter_id} does not exist."
            )

    update_data = job_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(job, field, value)
        
    await job.save()
    
    await log_action(
        action="UPDATE_JOB",
        details=f"Updated job listing: {job.title} (id: {job.id})",
        user=current_user,
        request=request
    )
    return job


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_job(
    job_id: str,
    request: Request,
    current_user: User = Depends(PermissionChecker("manage_jobs"))
) -> None:
    """
    Remove a job listing permanently.
    Requires 'manage_jobs' permission.
    """
    job = await Job.get(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job listing not found",
        )
    title = job.title
    await job.delete()
    
    await log_action(
        action="DELETE_JOB",
        details=f"Deleted job listing: {title} (id: {job_id})",
        user=current_user,
        request=request
    )
    return None
