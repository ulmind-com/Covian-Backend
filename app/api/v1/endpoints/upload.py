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
        # Preserve the original file extension in the public_id so the delivered
        # URL ends in .pdf/.doc/.docx. Without this, raw uploads get an
        # extension-less URL and the viewer can't tell what content type it is
        # (which makes real PDFs fail to render with "Failed to load PDF document").
        import os
        import uuid
        ext = os.path.splitext(file.filename or "")[1].lower()
        if ext not in (".pdf", ".doc", ".docx"):
            ext = ".pdf"
        public_id = f"cv_{uuid.uuid4().hex}{ext}"

        result = cloudinary.uploader.upload(
            contents,
            folder="corevita_cvs",
            resource_type="raw",
            public_id=public_id,
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
    Proxy endpoint that downloads a CV from Cloudinary and streams it to the
    client. Accepts token as query param so it can be used in iframes and
    direct links (since iframes can't send Authorization headers).
    """
    from app.core.security import verify_token
    from app.models.user import User as UserModel

    # Manually verify the token (since iframes can't send Authorization headers)
    user_id = verify_token(token, is_refresh=False)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    try:
        from beanie import PydanticObjectId
        user = await UserModel.get(PydanticObjectId(user_id))
    except Exception:
        user = None

    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    if user.role not in ["SUPER_ADMIN", "ADMIN", "RECRUITER"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    import re
    import httpx
    from fastapi.responses import StreamingResponse

    # Validate it's a Cloudinary URL
    if 'res.cloudinary.com' not in cv_url and 'cloudinary' not in cv_url:
        raise HTTPException(status_code=400, detail="Invalid Cloudinary URL format")

    # Extract filename from URL for Content-Disposition header
    url_path = cv_url.split('?')[0]  # Strip query params
    filename = url_path.split('/')[-1] if '/' in url_path else 'resume.pdf'

    # Determine content type from file extension
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else 'pdf'
    content_type_map = {
        'pdf': 'application/pdf',
        'doc': 'application/msword',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    }
    content_type = content_type_map.get(ext, 'application/pdf')

    try:
        # Try to directly fetch the CV from Cloudinary first
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(cv_url)

            # If direct access is blocked (401/403), generate an authenticated URL
            if response.status_code in (401, 403):
                # Extract public_id and resource type from the Cloudinary URL
                match = re.search(
                    r'res\.cloudinary\.com/[^/]+/(image|raw)/upload/(?:v\d+/)?(.+)$',
                    cv_url,
                )
                if not match:
                    raise HTTPException(
                        status_code=400,
                        detail="Could not parse Cloudinary URL for authenticated download"
                    )

                resource_type = match.group(1)
                public_id_with_ext = match.group(2)
                if '.' in public_id_with_ext:
                    public_id, file_format = public_id_with_ext.rsplit('.', 1)
                else:
                    public_id = public_id_with_ext
                    file_format = "pdf"

                # Generate a signed private download URL
                download_url = cloudinary.utils.private_download_url(
                    public_id,
                    file_format,
                    resource_type=resource_type,
                    attachment=False,
                )
                response = await client.get(download_url, follow_redirects=True)

                # If private_download_url fails, try with cloudinary_url signed
                if response.status_code != 200:
                    signed_url, _ = cloudinary.utils.cloudinary_url(
                        public_id,
                        resource_type=resource_type,
                        type="authenticated",
                        format=file_format,
                        sign_url=True,
                    )
                    response = await client.get(signed_url, follow_redirects=True)

            if response.status_code != 200:
                raise HTTPException(
                    status_code=502,
                    detail=f"Failed to fetch CV from storage (HTTP {response.status_code})"
                )

            # Detect the real content type from the file's magic bytes instead of
            # blindly trusting the extension. This prevents a DOCX (or any non-PDF
            # file) from being served as application/pdf, which is what causes the
            # browser PDF viewer to show "Failed to load PDF document".
            head = response.content[:8]
            if head.startswith(b"%PDF"):
                content_type = "application/pdf"
            elif head[:2] == b"PK":
                content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            elif head[:8] == b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1":
                content_type = "application/msword"

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
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to proxy CV download: {str(e)}")
