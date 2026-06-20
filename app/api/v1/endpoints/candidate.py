from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from app.api.deps import get_current_active_user, RoleChecker, PermissionChecker
from app.models.candidate import Candidate
from app.models.application import Application
from app.models.candidate_timeline import CandidateTimeline
from app.models.job import Job
from app.models.user import User
from app.schemas.platform import (
    CandidateCreate, CandidateUpdate, CandidateResponse,
    ApplicationCreate, ApplicationUpdate, ApplicationResponse, PublicApplicationCreate,
    CandidateTimelineResponse,
)
from app.utils.audit import log_action
from app.utils.activity import log_activity
from app.utils.timeline import add_candidate_timeline_event
from app.utils.workflow_engine import trigger_workflow_event

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


# ==============================================================================
# APPLICATIONS MANAGEMENT
# ==============================================================================

@router.post("/public-apply", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def public_apply(
    app_in: PublicApplicationCreate,
    request: Request
) -> Any:
    """
    Public endpoint for candidates to apply to a job directly from the frontend.
    Does not require authentication.
    """
    # Verify job exists
    job = await Job.get(app_in.job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job ID {app_in.job_id} does not exist."
        )

    # Find existing candidate by email or create new
    candidate = await Candidate.find_one(Candidate.email == app_in.email)
    if not candidate:
        candidate = Candidate(
            name=app_in.name,
            email=app_in.email,
            phone=app_in.phone,
            skills=app_in.skills,
            cv_url=app_in.cv_url,
            status="AVAILABLE"
        )
        await candidate.insert()
    else:
        # Update existing candidate details
        candidate.name = app_in.name
        if app_in.phone:
            candidate.phone = app_in.phone
        if app_in.cv_url:
            candidate.cv_url = app_in.cv_url
        if app_in.skills:
            # Merge unique skills
            candidate.skills = list(set(candidate.skills + app_in.skills))
        await candidate.save()

    # Check if application already exists for this job
    existing_app = await Application.find_one(
        Application.job_id == app_in.job_id,
        Application.candidate_id == str(candidate.id)
    )
    if existing_app:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already applied for this position."
        )

    application = Application(
        job_id=app_in.job_id,
        candidate_id=str(candidate.id),
        current_stage="Applied",
        notes=[],
    )
    await application.insert()
    
    # Enqueue background email notification to candidate
    from app.utils.background import enqueue_email_notification
    await enqueue_email_notification(
        recipient_email=candidate.email,
        title="Application Received - CoreVita Advisory",
        message=f"Hello {candidate.name},\n\nWe have received your application for the position: {job.title}. Our team is reviewing it and we will be in touch soon!"
    )

    # Get a dummy user or just None for actor
    from app.models.user import User
    system_user = await User.find_one({"email": "admin@corevita.com"}) # Use any admin or none

    # Log to candidate timeline
    await add_candidate_timeline_event(
        candidate_id=str(candidate.id),
        event_type="APPLICATION_CREATED",
        title=f"Applied to {job.title}",
        description=f"Application submitted for job '{job.title}'. Initial stage: {application.current_stage}.",
        actor=system_user,
        related_job_id=app_in.job_id,
        related_application_id=str(application.id),
    )

    # Log to activity feed
    await log_activity(
        event_type="APPLICATION_CREATED",
        entity_type="application",
        entity_id=str(application.id),
        title=f"New public application: {candidate.name} → {job.title}",
        description=f"Candidate {candidate.name} applied to job '{job.title}' via website.",
        actor=system_user,
    )

    return application

@router.get("/applications", response_model=List[ApplicationResponse])
async def list_applications(
    skip: int = 0,
    limit: int = 200,
    job_id: str = None,
    current_user: User = Depends(RoleChecker(["SUPER_ADMIN", "ADMIN", "RECRUITER"]))
) -> Any:
    """
    List all applications. Can be filtered by job_id.
    """
    query = {}
    if job_id:
        query["job_id"] = job_id
        
    apps = await Application.find(query).sort("-created_at").skip(skip).limit(limit).to_list()
    return apps

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

    # Log to candidate timeline
    await add_candidate_timeline_event(
        candidate_id=str(candidate.id),
        event_type="APPLICATION_CREATED",
        title=f"Applied to {job.title}",
        description=f"Application submitted for job '{job.title}'. Initial stage: {application.current_stage}.",
        actor=current_user,
        related_job_id=app_in.job_id,
        related_application_id=str(application.id),
    )

    # Log to activity feed
    await log_activity(
        event_type="APPLICATION_CREATED",
        entity_type="application",
        entity_id=str(application.id),
        title=f"New application: {candidate.name} → {job.title}",
        description=f"Candidate {candidate.name} applied to job '{job.title}'.",
        actor=current_user,
    )

    # Trigger workflow automation engine
    await trigger_workflow_event(
        event="APPLICATION_CREATED",
        payload={
            "application_id": str(application.id),
            "candidate_id": str(candidate.id),
            "candidate_email": candidate.email,
            "job_id": app_in.job_id,
            "job_title": job.title,
            "stage": application.current_stage,
        },
        actor=current_user,
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

    # Log stage change to candidate timeline
    await add_candidate_timeline_event(
        candidate_id=str(candidate.id),
        event_type="STAGE_CHANGED",
        title=f"Stage moved: {old_stage} → {app.current_stage}",
        description=f"Application for '{job.title}' advanced from '{old_stage}' to '{app.current_stage}'.",
        actor=current_user,
        related_job_id=app.job_id,
        related_application_id=str(app.id),
        metadata={"old_stage": old_stage, "new_stage": app.current_stage},
    )

    # Log to global activity feed
    await log_activity(
        event_type="CANDIDATE_STAGE_CHANGED",
        entity_type="application",
        entity_id=str(app.id),
        title=f"{candidate.name} → {app.current_stage} ({job.title})",
        description=f"Candidate '{candidate.name}' moved from '{old_stage}' to '{app.current_stage}' in job '{job.title}'.",
        actor=current_user,
        metadata={"old_stage": old_stage, "new_stage": app.current_stage},
    )

    # Trigger workflow automation engine
    await trigger_workflow_event(
        event="CANDIDATE_STAGE_CHANGED",
        payload={
            "application_id": str(app.id),
            "candidate_id": str(candidate.id),
            "candidate_email": candidate.email,
            "candidate_name": candidate.name,
            "job_id": app.job_id,
            "job_title": job.title,
            "old_stage": old_stage,
            "stage": app.current_stage,
        },
        actor=current_user,
    )

    await log_action(
        action="UPDATE_APPLICATION_STAGE",
        details=f"Moved application (id: {app.id}) to stage: {app.current_stage}",
        user=current_user,
        request=request
    )
    return app


# ==============================================================================
# CANDIDATE TIMELINE
# ==============================================================================

@router.get("/{candidate_id}/timeline", response_model=List[CandidateTimelineResponse])
async def get_candidate_timeline(
    candidate_id: str,
    limit: int = 100,
    current_user: User = Depends(RoleChecker(["SUPER_ADMIN", "ADMIN", "RECRUITER"]))
) -> Any:
    """
    Retrieve the full chronological event timeline for a specific candidate.
    Covers: application created, stage changes, notes, emails sent, and more.
    """
    candidate = await Candidate.get(candidate_id)
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found"
        )
    return await CandidateTimeline.find(
        CandidateTimeline.candidate_id == candidate_id
    ).sort("-created_at").limit(limit).to_list()
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


