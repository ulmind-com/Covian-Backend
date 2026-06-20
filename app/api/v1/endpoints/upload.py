"""
Cloudinary Image Upload Endpoint
=================================
Provides a single POST /upload endpoint that accepts a file,
uploads it to Cloudinary, and returns the secure URL.

Used by all admin forms (News, Team, Testimonials, Logos) for image uploads.
"""

import cloudinary
import cloudinary.uploader
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from app.api.deps import RoleChecker
from app.core.config import settings
from app.models.user import User

router = APIRouter()

# Configure Cloudinary on module load
cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True,
)


@router.post("/upload", tags=["Upload"])
async def upload_image(
    file: UploadFile = File(...),
    folder: str = "corevita",
    current_user: User = Depends(RoleChecker(["SUPER_ADMIN", "ADMIN", "EDITOR"])),
):
    """
    Upload an image to Cloudinary.
    Returns the secure URL of the uploaded image.

    - **file**: The image file (JPEG, PNG, WebP, GIF, SVG)
    - **folder**: Cloudinary folder name (default: "corevita")
    """
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/webp", "image/gif", "image/svg+xml"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{file.content_type}' not allowed. Use: JPEG, PNG, WebP, GIF, SVG"
        )

    # Validate file size (max 10MB)
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 10MB.")

    try:
        result = cloudinary.uploader.upload(
            contents,
            folder=folder,
            resource_type="image",
            transformation=[
                {"quality": "auto", "fetch_format": "auto"}
            ],
        )
        return {
            "url": result["secure_url"],
            "public_id": result["public_id"],
            "width": result.get("width"),
            "height": result.get("height"),
            "format": result.get("format"),
            "bytes": result.get("bytes"),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.delete("/upload/{public_id:path}", tags=["Upload"])
async def delete_image(
    public_id: str,
    current_user: User = Depends(RoleChecker(["SUPER_ADMIN", "ADMIN"])),
):
    """Delete an image from Cloudinary by public_id."""
    try:
        result = cloudinary.uploader.destroy(public_id)
        return {"result": result.get("result", "not found")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")

@router.post("/upload-cv", tags=["Upload"])
async def upload_cv(
    file: UploadFile = File(...),
):
    """
    Public endpoint to upload a Candidate CV to Cloudinary.
    Returns the secure URL of the uploaded document.
    Allows PDF and basic document formats.
    """
    allowed_types = ["application/pdf", "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{file.content_type}' not allowed. Use: PDF, DOC, DOCX"
        )

    # Validate file size (max 10MB)
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 10MB.")

    try:
        result = cloudinary.uploader.upload(
            contents,
            folder="corevita_cvs",
            resource_type="auto",
        )
        return {"url": result["secure_url"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
