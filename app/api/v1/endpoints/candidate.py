from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from app.api.deps import get_current_active_user, RoleChecker, PermissionChecker
from app.models.candidate import Candidate
from app.models.application import Application
from app.models.job import Job
from app.models.user import User
from app.schemas.platform import (
    CandidateCreate, CandidateUpdate, CandidateResponse,
    ApplicationCreate, ApplicationUpdate, ApplicationResponse
)
from app.utils.audit import log_action

router = APIRouter()


@router.post("/", response_model=CandidateResponse, status_code=status.HTTP_201_CREATED)
async def create_candidate(
    candidate_in: CandidateCreate,
    request: Request,
    current_user: User = Depends(PermissionChecker("manage_candidates"))
) -> Any:
    """
    Create a new candidate profile.
    Requires 'manage_candidates' permission.
    """
    # Verify unique email
    existing = await Candidate.find_one(Candidate.email == candidate_in.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A candidate with this email address already exists."
        )

    candidate = Candidate(
        name=candidate_in.name,
        email=candidate_in.email,
        phone=candidate_in.phone,
        skills=[s.strip() for s in candidate_in.skills],
        cv_url=candidate_in.cv_url,
        status=candidate_in.status,
    )
    await candidate.insert()
    
    await log_action(
        action="CREATE_CANDIDATE",
        details=f"Created candidate profile: {candidate.name} ({candidate.email})",
        user=current_user,
        request=request
    )
    return candidate


@router.get("/", response_model=List[CandidateResponse])
async def list_candidates(
    skip: int = 0,
    limit: int = 100,
    skills: str = None,  # comma-separated list
    status_filter: str = None,
    current_user: User = Depends(RoleChecker(["SUPER_ADMIN", "ADMIN", "RECRUITER"]))
) -> Any:
    """
    Fetch all candidates with pagination. Can filter by skills (comma-separated, matches all skills) and status.
    Accessible to admins and recruiters.
    """
    query = {}
    if status_filter:
        query["status"] = status_filter
        
    if skills:
        skill_list = [s.strip() for s in skills.split(",")]
        # Match documents where 'skills' contains all the specified elements (highly performant indexed search)
        query["skills"] = {"$all": skill_list}
        
    return await Candidate.find(query).skip(skip).limit(limit).to_list()


@router.get("/{candidate_id}", response_model=CandidateResponse)
async def get_candidate_by_id(
    candidate_id: str,
    current_user: User = Depends(RoleChecker(["SUPER_ADMIN", "ADMIN", "RECRUITER"]))
) -> Any:
    """
    Retrieve candidate profile by ID.
    """
    candidate = await Candidate.get(candidate_id)
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate profile not found",
        )
    return candidate


@router.put("/{candidate_id}", response_model=CandidateResponse)
async def update_candidate(
    candidate_id: str,
    candidate_in: CandidateUpdate,
    request: Request,
    current_user: User = Depends(PermissionChecker("manage_candidates"))
) -> Any:
    """
    Modify candidate profile details or skills.
    Requires 'manage_candidates' permission.
    """
    candidate = await Candidate.get(candidate_id)
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate profile not found",
        )
        
    update_data = candidate_in.model_dump(exclude_unset=True)
    if "skills" in update_data:
        update_data["skills"] = [s.strip() for s in update_data["skills"]]
        
    for field, value in update_data.items():
        setattr(candidate, field, value)
        
    await candidate.save()
    
    await log_action(
        action="UPDATE_CANDIDATE",
        details=f"Updated candidate: {candidate.name} (id: {candidate.id})",
        user=current_user,
        request=request
    )
    return candidate


@router.delete("/{candidate_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_candidate(
    candidate_id: str,
    request: Request,
    current_user: User = Depends(PermissionChecker("manage_candidates"))
) -> None:
    """
    Delete a candidate profile.
    Requires 'manage_candidates' permission.
    """
    candidate = await Candidate.get(candidate_id)
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate profile not found",
        )
    name = candidate.name
    await candidate.delete()
    
    await log_action(
        action="DELETE_CANDIDATE",
        details=f"Deleted candidate profile: {name} (id: {candidate_id})",
        user=current_user,
        request=request
    )
    return None


# ==============================================================================
# APPLICATIONS MANAGEMENT
# ==============================================================================

@router.post("/applications", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def create_application(
    app_in: ApplicationCreate,
    request: Request,
    current_user: User = Depends(PermissionChecker("manage_candidates"))
) -> Any:
    """
    Submit a candidate application for an open job.
    """
    # Verify job and candidate exist
    job = await Job.get(app_in.job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job ID {app_in.job_id} does not exist."
        )
    candidate = await Candidate.get(app_in.candidate_id)
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Candidate ID {app_in.candidate_id} does not exist."
        )

    application = Application(
        job_id=app_in.job_id,
        candidate_id=app_in.candidate_id,
        current_stage=app_in.current_stage,
        notes=app_in.notes,
    )
    await application.insert()
    
    # Enqueue background email notification to candidate
    from app.utils.background import enqueue_email_notification
    await enqueue_email_notification(
        recipient_email=candidate.email,
        title="Application Received - CoreVita Advisory",
        message=f"Hello {candidate.name},\n\nWe have received your application for the position: {job.title}. Our team is reviewing it and we will be in touch soon!"
    )
    
    await log_action(
        action="CREATE_APPLICATION",
        details=f"Submitted application for candidate {candidate.name} to job {job.title}",
        user=current_user,
        request=request
    )
    return application


@router.get("/applications/{application_id}", response_model=ApplicationResponse)
async def get_application(
    application_id: str,
    current_user: User = Depends(RoleChecker(["SUPER_ADMIN", "ADMIN", "RECRUITER"]))
) -> Any:
    """
    Get job application details.
    """
    app = await Application.get(application_id)
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    return app


@router.put("/applications/{application_id}", response_model=ApplicationResponse)
async def update_application(
    application_id: str,
    app_in: ApplicationUpdate,
    request: Request,
    current_user: User = Depends(PermissionChecker("manage_candidates"))
) -> Any:
    """
    Move the candidate application through different pipeline stages (e.g. Screened -> Interviewing).
    """
    app = await Application.get(application_id)
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
        
    job = await Job.get(app.job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Associated job not found"
        )
        
    candidate = await Candidate.get(app.candidate_id)
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Associated candidate not found"
        )
        
    if app_in.current_stage not in job.pipeline_stages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stage '{app_in.current_stage}' is not a valid stage in this job's pipeline. Allowed stages: {job.pipeline_stages}"
        )

    old_stage = app.current_stage
    app.current_stage = app_in.current_stage
    if app_in.notes is not None:
        app.notes.extend(app_in.notes)
        
    await app.save()
    
    # Enqueue background email notification to candidate
    from app.utils.background import enqueue_email_notification
    await enqueue_email_notification(
        recipient_email=candidate.email,
        title="Application Status Updated - CoreVita Advisory",
        message=f"Hello {candidate.name},\n\nYour application status for '{job.title}' has been updated from '{old_stage}' to '{app.current_stage}'."
    )
    
    await log_action(
        action="UPDATE_APPLICATION_STAGE",
        details=f"Moved application (id: {app.id}) to stage: {app.current_stage}",
        user=current_user,
        request=request
    )
    return app

