import time
from fastapi import APIRouter, Body, Depends, HTTPException, Query, Path, status
from typing import List, Optional
import json
from schemas.imports import ListOfCategories, SearchQuery
from schemas.response_schema import APIResponse
from sub_app1.services.blog import search_blogs_service    
from sub_app1.services.utils import get_path_filter, get_sort
from sub_app1.schemas.imports import BlogType, SortType
from schemas.blog import (
 
    BlogOutLessDetailUserVersion,
    BlogOutUserVersion,
 
  
    CategorySlugEnum,
    CategoryNameEnum,
    BlogStatus,
    Category,
    CATEGORY_PAIRS,
    ListOfBlogs,
    ListOfBlogsWithSameCategories
)
from services.blog_service import (
    add_blog,
    remove_blog,
    retrieve_blogs,
    retrieve_blog_by_blog_id,
    update_blog_by_id,
)

router = APIRouter(prefix="/content",)

# This is a mandatory filter applied to all blog-retrieving GET endpoints.
PUBLISHED_FILTER = {"state": BlogStatus.published.value}

# -------------------------------------------------------------------
# List all available categories
# (This endpoint is not for blogs, so it remains unchanged)
# -------------------------------------------------------------------
@router.get("/categories", response_model=APIResponse[ListOfCategories])
async def list_all_categories():
    """
    Retrieves a list of all available blog categories and their slugs.
    """
    total = len(CATEGORY_PAIRS)

    categories = [
        Category(
            name=name,
            slug=slug,
            itemIndex=i,
           
        )
        for i, (name, slug) in enumerate(CATEGORY_PAIRS.items(), start=1)
    ]
    listOfCategories =ListOfCategories(listOfCategories=categories,totalItems=total)
    return APIResponse(
        status_code=200,
        data=listOfCategories,
        detail="Successfully retrieved all categories."
    )
    
# -------------------------------------------------------------------
# Get *Published* Blogs by BlogType
# -------------------------------------------------------------------
@router.get("/by-blog-type/{blog_type}", response_model=APIResponse[ListOfBlogs])
async def list_blogs_by_blog_type(
    blog_type: BlogType = Path(..., description="The type of blog to filter by"),
    start: Optional[int] = Query(0, description="Start index for pagination"),
    stop: Optional[int] = Query(50, description="Stop index for pagination"),
    sort: Optional[SortType] = Query(SortType.newest,description='Optional Sort string describing MongoDB sort instructions ')
):
    """
    Retrieves *published* blogs filtered by a specific `BlogType`.
    Supports additional filtering and pagination.
    """
    
    try:
        path_filter= get_path_filter(blog_type=blog_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"This is from the get path filter {e}")
    
    parsed_filters = {}
     
    # Merge filters: Path and Published status always override query filters
    final_filters = parsed_filters.copy()
    final_filters.update(path_filter)
    final_filters.update(PUBLISHED_FILTER) # Enforce published
    sort_info = get_sort(sort.value)
    field = sort_info["sort_field"]
    order = sort_info["sort_order"]
    items = await retrieve_blogs(
        filters=final_filters,
        start=start,
        stop=stop,
        sort_field=field,
        sort_order=order
    )
    blogs = ListOfBlogs(
    blogs=[BlogOutLessDetailUserVersion(**item.model_dump()) for item in items],
    totalItems=len(items)
)
    return APIResponse(
        status_code=200,
        data=blogs,
        detail=f"Fetched published blogs with type '{blog_type.value}'"
    )

# -------------------------------------------------------------------
# Get *Published* Blogs by Category Slug
# -------------------------------------------------------------------
@router.get("/by-category-slug/{slug}",  response_model=APIResponse[ListOfBlogsWithSameCategories])
async def list_blogs_by_category_slug(
    slug: CategorySlugEnum = Path(..., description="The category slug to filter by"),
    start: Optional[int] = Query(0, description="Start index for pagination"),
    stop: Optional[int] = Query(50, description="Stop index for pagination"),
    sort: Optional[SortType] = Query(SortType.newest,description='Optional Sort string describing MongoDB sort instructions ')
):
    """
    Retrieves *published* blogs filtered by a specific `category.slug`.
    Supports additional filtering and pagination.
    """
    path_filter = {"category.slug": slug.value}
    
    parsed_filters = {}
 
            
    final_filters = parsed_filters.copy()
    final_filters.update(path_filter)
    final_filters.update(PUBLISHED_FILTER) # Enforce published
    sort_info = get_sort(sort.value)
    field = sort_info["sort_field"]
    order = sort_info["sort_order"]
    items = await retrieve_blogs(
        filters=final_filters,
        start=start,
        stop=stop,
        sort_field=field,
        sort_order=order
    )
    list_of_blogs = ListOfBlogsWithSameCategories( 
        blogs=[BlogOutLessDetailUserVersion(**item.model_dump()) for item in items],
        totalItems=len(items),
        category=items[0].category.name if items else None )
    return APIResponse(
        status_code=200,
        data=list_of_blogs,
        detail=f"Fetched published blogs with category slug '{slug.value}'"
    )

# -------------------------------------------------------------------
# Get *Published* Blogs by Author Name
# -------------------------------------------------------------------
@router.get("/by-author-name",  response_model=APIResponse[ListOfBlogs])
async def list_blogs_by_author_name(
    author_name: str = Query(..., description="The author name to filter by (exact match)"),
    start: Optional[int] = Query(0, description="Start index for pagination"),
    stop: Optional[int] = Query(50, description="Stop index for pagination"),
    sort: Optional[SortType] = Query(SortType.newest,description='Optional Sort string describing MongoDB sort instructions ')
):
    """
    Retrieves *published* blogs filtered by a specific `author.name`.
    Supports additional filtering and pagination.
    """
    path_filter = {"author.name": author_name}
    
    parsed_filters = {}
   
    final_filters = parsed_filters.copy()
    final_filters.update(path_filter)
    final_filters.update(PUBLISHED_FILTER) # Enforce published
    
    sort_info = get_sort(sort.value)
    field = sort_info["sort_field"]
    order = sort_info["sort_order"]
    
    items = await retrieve_blogs(
        filters=final_filters,
        start=start,
        stop=stop,
        sort_field=field,
        sort_order=order
    )
    blogs = ListOfBlogs(
    blogs=[BlogOutLessDetailUserVersion(**item.model_dump()) for item in items],
    totalItems=len(items)
)
    return APIResponse(
        status_code=200,
        data=blogs,
        detail=f"Fetched published blogs by author '{author_name}'"
    )

# -------------------------------------------------------------------
# --- ORIGINAL GET ENDPOINTS (MODIFIED FOR 'PUBLISHED' STATE) ---
# -------------------------------------------------------------------


# ------------------------------
# List *Published* Blogs
# ------------------------------
@router.get("/", response_model=APIResponse[ListOfBlogs])
async def list_blogs(
    start: Optional[int] = Query(0, description="Start index for range-based pagination"),
    stop: Optional[int] = Query(100, description="Stop index for range-based pagination"),
    sort: Optional[SortType] = Query(SortType.newest,description='Optional Sort string describing MongoDB sort instructions ')
):
    """
    Retrieves a list of *published* Blogs with pagination and optional filtering.
    """
    parsed_filters = {}

    final_filters = parsed_filters.copy()
    final_filters.update(PUBLISHED_FILTER) # Enforce published
    sort_info = get_sort(sort.value)
    field = sort_info["sort_field"]
    order = sort_info["sort_order"]
    # Determine Pagination
    if start is not None or stop is not None:
        if start is None or stop is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Both 'start' and 'stop' must be provided together.")
        if stop < start:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="'stop' cannot be less than 'start'.")
        
        items = await retrieve_blogs(filters=final_filters, start=start, stop=stop,sort_field=field,sort_order=order)
        detail_msg = "Fetched published blogs successfully"
    else:
        items = await retrieve_blogs(filters=final_filters, start=0, stop=100,sort_field=field,sort_order=order)
        detail_msg = "Fetched first 100 published records successfully"
        
    if parsed_filters:
        detail_msg += " (with additional filters applied)"
    blogs = ListOfBlogs(
    blogs=[BlogOutLessDetailUserVersion(**item.model_dump()) for item in items],
    totalItems=len(items)
)
    return APIResponse(status_code=200, data=blogs, detail=detail_msg)


# ------------------------------
# Retrieve a single *Published* Blog
# ------------------------------
@router.get("/{id}", response_model=APIResponse[BlogOutUserVersion])
async def get_blog_by_id(
    id: str = Path(..., description="blog ID to fetch specific item")
):
    """
    Retrieves a single *published* Blog by its ID.
    Returns 404 if the blog is not found or is not published.
    """
    item = await retrieve_blog_by_blog_id(id=id)
    
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Blog not found")
        
    # Enforce published state
    # We use 404 to avoid leaking the existence of a draft
    if item.state != BlogStatus.published:
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Blog not found or is not published"
        )
            
    return APIResponse(status_code=200, data=item, detail="blog item fetched")

# ------------------------------------------------
# Searches and returns Multiple *Published* Blogs
# ------------------------------------------------
@router.get(
    "/search/",
 
    summary="Search blog articles by keywords",
    description="Finds and ranks published articles by title or author with pagination."
)
async def search_published_blogs(
    query_params: SearchQuery = Depends()
):
    """
    Executes the MongoDB search using regex on title and/or author.
    """

 
    # 2. Service Call
    search_results = await search_blogs_service(query_params)

    # 3. Response Formatting
    return APIResponse(
        status_code=200,
        data=search_results,
        detail=f"Found {search_results.totalItems} matching blog items."
    )
