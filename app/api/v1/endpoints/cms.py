from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from app.api.deps import get_current_active_user, RoleChecker, PermissionChecker
from app.models.cms import CMSPage, CMSBlog, CMSService
from app.models.user import User
from app.schemas.platform import (
    CMSPageCreate, CMSPageResponse,
    CMSBlogCreate, CMSBlogResponse,
    CMSServiceCreate, CMSServiceResponse
)
from app.utils.audit import log_action

router = APIRouter()

# ==============================================================================
# PAGES COLLECTION
# ==============================================================================

@router.post("/pages", response_model=CMSPageResponse, status_code=status.HTTP_201_CREATED)
async def create_cms_page(
    page_in: CMSPageCreate,
    request: Request,
    current_user: User = Depends(PermissionChecker("manage_cms"))
) -> Any:
    """
    Create a new dynamic platform page. Slug must be unique.
    """
    existing = await CMSPage.find_one(CMSPage.slug == page_in.slug)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"CMS page with slug '{page_in.slug}' already exists."
        )
    page = CMSPage(
        slug=page_in.slug,
        title=page_in.title,
        content=page_in.content,
    )
    await page.insert()
    
    await log_action(
        action="CREATE_CMS_PAGE",
        details=f"Created CMS Page: {page.title} (slug: {page.slug})",
        user=current_user,
        request=request
    )
    return page


@router.get("/pages", response_model=List[CMSPageResponse])
async def list_cms_pages() -> Any:
    """
    Public endpoint to list all platform pages.
    """
    return await CMSPage.find_all().to_list()


@router.get("/pages/{slug}", response_model=CMSPageResponse)
async def get_cms_page_by_slug(slug: str) -> Any:
    """
    Public endpoint to fetch a platform page by its slug.
    """
    page = await CMSPage.find_one(CMSPage.slug == slug)
    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CMS Page not found."
        )
    return page


@router.delete("/pages/{slug}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cms_page(
    slug: str,
    request: Request,
    current_user: User = Depends(PermissionChecker("manage_cms"))
) -> Any:
    """
    Remove a platform page permanently.
    """
    page = await CMSPage.find_one(CMSPage.slug == slug)
    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CMS Page not found."
        )
    title = page.title
    await page.delete()
    
    await log_action(
        action="DELETE_CMS_PAGE",
        details=f"Deleted CMS Page: {title} (slug: {slug})",
        user=current_user,
        request=request
    )
    return None


# ==============================================================================
# BLOGS COLLECTION
# ==============================================================================

@router.post("/blogs", response_model=CMSBlogResponse, status_code=status.HTTP_201_CREATED)
async def create_cms_blog(
    blog_in: CMSBlogCreate,
    request: Request,
    current_user: User = Depends(PermissionChecker("manage_cms"))
) -> Any:
    """
    Publish a new blog post.
    """
    existing = await CMSBlog.find_one(CMSBlog.slug == blog_in.slug)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"CMS blog post with slug '{blog_in.slug}' already exists."
        )
    blog = CMSBlog(
        slug=blog_in.slug,
        title=blog_in.title,
        content=blog_in.content,
        author=blog_in.author,
    )
    await blog.insert()
    
    await log_action(
        action="CREATE_CMS_BLOG",
        details=f"Published CMS Blog: {blog.title} (slug: {blog.slug})",
        user=current_user,
        request=request
    )
    return blog


@router.get("/blogs", response_model=List[CMSBlogResponse])
async def list_cms_blogs() -> Any:
    """
    Public endpoint to fetch published blog posts.
    """
    return await CMSBlog.find_all().to_list()


@router.get("/blogs/{slug}", response_model=CMSBlogResponse)
async def get_cms_blog_by_slug(slug: str) -> Any:
    """
    Public endpoint to get a blog post by its slug.
    """
    blog = await CMSBlog.find_one(CMSBlog.slug == slug)
    if not blog:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CMS Blog not found."
        )
    return blog


# ==============================================================================
# SERVICES COLLECTION
# ==============================================================================

@router.post("/services", response_model=CMSServiceResponse, status_code=status.HTTP_201_CREATED)
async def create_cms_service(
    service_in: CMSServiceCreate,
    request: Request,
    current_user: User = Depends(PermissionChecker("manage_cms"))
) -> Any:
    """
    Add a new advisory or consulting workforce program.
    """
    service = CMSService(
        name=service_in.name,
        description=service_in.description,
        price=service_in.price,
    )
    await service.insert()
    
    await log_action(
        action="CREATE_CMS_SERVICE",
        details=f"Created CMS Service program: {service.name}",
        user=current_user,
        request=request
    )
    return service


@router.get("/services", response_model=List[CMSServiceResponse])
async def list_cms_services() -> Any:
    """
    Public endpoint to retrieve standard service programs.
    """
    return await CMSService.find_all().to_list()
