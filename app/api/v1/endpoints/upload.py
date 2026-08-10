"""
Cloudinary Image Upload Endpoint
=================================
Provides a single POST /upload endpoint that accepts a file,
uploads it to Cloudinary, and returns the secure URL.

Used by all admin forms (News, Team, Testimonials, Logos) for image uploads.
"""

import cloudinary
import cloudinary.uploader
import cloudinary.utils
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Query
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
            resource_type="raw",
        )
        return {"url": result["secure_url"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/proxy-cv", tags=["Upload"])
async def proxy_cv_download(
    cv_url: str = Query(..., description="The original Cloudinary CV URL"),
    token: str = Query(..., description="JWT access token for authentication"),
):
    """
    Proxy endpoint that downloads a CV from Cloudinary using the private
    download API and streams it to the client. This bypasses Cloudinary ACL
    restrictions that block direct browser access to uploaded files.
    Accepts token as query param so it can be used in iframes and direct links.
    """
    from app.core.security import verify_token
    from app.models.user import User as UserModel

    # Manually verify the token (since iframes can't send Authorization headers)
    user_id = verify_token(token, is_refresh=False)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = await UserModel.get(user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    if user.role not in ["SUPER_ADMIN", "ADMIN", "RECRUITER"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    import re
    import httpx
    from fastapi.responses import StreamingResponse

    # Extract public_id and format from the Cloudinary URL
    match = re.search(r'res\.cloudinary\.com/[^/]+/(image|raw)/upload/(?:v\d+/)?(.+)$', cv_url)
    if not match:
        raise HTTPException(status_code=400, detail="Invalid Cloudinary URL format")

    resource_type = match.group(1)
    public_id_with_ext = match.group(2)

    # Split public_id and file extension
    if '.' in public_id_with_ext:
        public_id, file_format = public_id_with_ext.rsplit('.', 1)
    else:
        public_id = public_id_with_ext
        file_format = "pdf"

    try:
        # Generate a private download URL using Cloudinary's API
        # This creates a server-signed URL that bypasses ACL restrictions
        download_url = cloudinary.utils.private_download_url(
            public_id,
            file_format,
            resource_type=resource_type,
            type="upload",
            attachment=True,
        )

        # Fetch the file from the private download URL
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(download_url, follow_redirects=True)

            if response.status_code != 200:
                raise HTTPException(
                    status_code=502,
                    detail=f"Failed to fetch CV from storage (HTTP {response.status_code})"
                )

            # Determine filename
            filename = public_id_with_ext.split('/')[-1] if '/' in public_id_with_ext else public_id_with_ext

            content_type = response.headers.get("content-type", "application/pdf")

            return StreamingResponse(
                iter([response.content]),
                media_type=content_type,
                headers={
                    "Content-Disposition": f'inline; filename="{filename}"',
                    "Content-Length": str(len(response.content)),
                },
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to proxy CV download: {str(e)}")
