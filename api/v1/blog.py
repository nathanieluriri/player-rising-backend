
import time
from fastapi import APIRouter, Body, HTTPException, Query, Path, status
from typing import List, Optional
import json
from schemas.imports import CATEGORY_PAIRS, Category
from schemas.response_schema import APIResponse
from schemas.blog import (
    BlogCreate,
    BlogOut,
    BlogBase,
    BlogUpdate,
)
from services.blog_service import (
    add_blog,
    remove_blog,
    retrieve_blogs,
    retrieve_blog_by_blog_id,
    update_blog_by_id,
)

router = APIRouter(prefix="/blogs", tags=["Blogs"])

# ------------------------------
# List Most Recent Blogs (with optional filters & pagination)
# ------------------------------
@router.get("/recent", response_model=APIResponse[List[BlogOut]])
async def list_most_recent_blogs(
    start: Optional[int] = Query(0, description="Start index for range-based pagination"),
    stop: Optional[int] = Query(50, description="Stop index for range-based pagination"),
    filters: Optional[str] = Query(None, description="Optional JSON string of MongoDB filter criteria (e.g., '{\"field\": \"value\"}')")
):
    """
    Retrieves a list of the most recent Blogs, sorted by `date_created` descending.
    Supports optional filtering and range-based pagination.
    
    - `start`/`stop`: Range-based pagination (like slicing)
    - `filters`: JSON string of MongoDB query filters
    """
    parsed_filters = {}

    # Parse filters if provided
    if filters:
        try:
            parsed_filters = json.loads(filters)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON format for 'filters' query parameter."
            )

    # Validate start/stop
    if start is not None or stop is not None:
        if start is None or stop is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Both 'start' and 'stop' must be provided together.")
        if stop < start:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="'stop' cannot be less than 'start'.")

    # Retrieve items from DB (service layer should handle sorting by date_created descending)
    items = await retrieve_blogs(
        filters=parsed_filters,
        start=start or 0,
        stop=stop or 50,
        sort_field="date_created",
        sort_order=-1  # descending
    )

    detail_msg = f"Fetched blogs {start} to {stop} sorted by most recent"
    if parsed_filters:
        detail_msg += " (with filters applied)"

    return APIResponse(status_code=200, data=items, detail=detail_msg)

# ------------------------------
# List Blogs (with pagination and filtering)
# ------------------------------
@router.get("/", response_model=APIResponse[List[BlogOut]])
async def list_blogs(
    start: Optional[int] = Query(0, description="Start index for range-based pagination"),
    stop: Optional[int] = Query(100, description="Stop index for range-based pagination"),
   
    # New: Filter parameter expects a JSON string
    filters: Optional[str] = Query('{"field":"value"}', description="Optional JSON string of MongoDB filter criteria (e.g., '{\"field\": \"value\"}')")
):
    """
    Retrieves a list of Blogs with pagination and optional filtering.
    - Priority 1: Range-based (start/stop)
    - Priority 2: Page-based (page_number)
    - Priority 3: Default (first 100)
    """
    PAGE_SIZE = 50
    parsed_filters = {}

    # 1. Handle Filters
    if filters:
        try:
            parsed_filters = json.loads(filters)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON format for 'filters' query parameter."
            )

    # 2. Determine Pagination
    # Case 1: Prefer start/stop if provided
    if start is not None or stop is not None:
        if start is None or stop is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Both 'start' and 'stop' must be provided together.")
        if stop < start:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="'stop' cannot be less than 'start'.")
        
        # Pass filters to the service layer
        items = await retrieve_blogs(filters=parsed_filters, start=start, stop=stop)
        return APIResponse(status_code=200, data=items, detail="Fetched successfully")

    # Case 3: Default (no params)
    else:
        # Pass filters to the service layer
        items = await retrieve_blogs(filters=parsed_filters, start=0, stop=100)
        detail_msg = "Fetched first 100 records successfully"
        if parsed_filters:
            # If filters were applied, adjust the detail message
            detail_msg = f"Fetched first 100 records successfully (with filters applied)"
        return APIResponse(status_code=200, data=items, detail=detail_msg)


# ------------------------------
# Retrieve a single Blog
# ------------------------------
@router.get("/{id}", response_model=APIResponse[BlogOut])
async def get_blog_by_id(
    id: str = Path(..., description="blog ID to fetch specific item")
):
    """
    Retrieves a single Blog by its ID.
    """
    item = await retrieve_blog_by_blog_id(id=id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Blog not found")
    return APIResponse(status_code=200, data=item, detail="blog item fetched")


# ------------------------------
# Create a new Blog
# ------------------------------
# Uses BlogBase for input (correctly)
@router.post(
    "/",
    response_model=APIResponse[BlogOut],
    status_code=status.HTTP_201_CREATED
)

async def create_blog(
    payload: BlogBase
):
    """
    Creates a new Blog.
    """
    # Creates BlogCreate object which includes date_created/last_updated
    new_data = BlogCreate(**payload.model_dump()) 
    new_item = await add_blog(new_data)
    if not new_item:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to create blog")
    
    return APIResponse(status_code=201, data=new_item, detail=f"Blog created successfully")


# ------------------------------
# Update an existing Blog
# ------------------------------
# Uses PATCH for partial update (correctly)
@router.patch(
    "/{id}",
    response_model=APIResponse[BlogOut]
)
async def update_blog(
    payload: BlogUpdate,
    id: str = Path(..., description="ID of the blog to update")
    
        
    
):
    """
    Updates an existing Blog by its ID.
    Assumes the service layer handles partial updates (e.g., ignores None fields in payload).
    """
    if payload.currentPageBody==[]:
        raise HTTPException(status_code=status.HTTP_202_ACCEPTED, detail=f"No update made")
    updated_item = await update_blog_by_id(blog_id=id, blog_data=payload)
    if not updated_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Blog not found or update failed")
    
    return APIResponse(status_code=200, data=updated_item, detail=f"Blog updated successfully")


# ------------------------------
# Delete an existing Blog
# ------------------------------
@router.delete("/{id}", response_model=APIResponse[None])
async def delete_blog(id: str = Path(..., description="ID of the blog to delete")):
    """
    Deletes an existing Blog by its ID.
    """
    deleted = await remove_blog(id)
    if not deleted:
        # This assumes remove_blog returns a boolean or similar
        # to indicate if deletion was successful (i.e., item was found).
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Blog not found or deletion failed")
    
    return APIResponse(status_code=200, data=None, detail=f"Blog deleted successfully")



# -------------------------------------------------------------------
# List all available categories
# (This endpoint is not for blogs, so it remains unchanged)
# -------------------------------------------------------------------
@router.get("/categories", response_model=APIResponse[List[Category]])
async def list_all_categories():
    """
    Retrieves a list of all available blog categories and their slugs.
    """
    categories = [
        Category(name=name, slug=slug) for name, slug in CATEGORY_PAIRS.items()
    ]
    return APIResponse(
        status_code=200,
        data=categories,
        detail="Successfully retrieved all categories."
    )