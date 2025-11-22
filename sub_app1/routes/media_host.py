import json
from typing import List, Literal, Optional
from fastapi import APIRouter, HTTPException, Query, Path, status
from repositories.media_host import get_media,get_media_files, MediaOut
from schemas.imports import CategoryNameEnum
from schemas.media_host import ListOfMediaOut
from schemas.response_schema import APIResponse
# Define Router
router = APIRouter()

# -------------------------------------------------------------------
# Get Media by Type (e.g., 'video', 'image')
# -------------------------------------------------------------------
@router.get("/by-type/{media_type}", response_model=APIResponse[ListOfMediaOut])
async def list_media_by_type(
    media_type: Literal["video","image"] = Path(..., description="The type of media (e.g., 'video', 'image')"),
    start: Optional[int] = Query(0, description="Start index for pagination"),
    stop: Optional[int] = Query(50, description="Stop index for pagination"),
    filters: Optional[str] = Query(None, description="Optional JSON string of additional MongoDB filter criteria")
):
    """
    Retrieves media files filtered by a specific `mediaType`.
    """
    path_filter = {"mediaType": media_type}
    
    parsed_filters = {}
    if filters:
        try:
            parsed_filters = json.loads(filters)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON format for 'filters' query parameter."
            )
            
    # Merge filters: Path filter overrides query filters
    final_filters = parsed_filters.copy()
    final_filters.update(path_filter)

    # Validate pagination
    if stop < start:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="'stop' cannot be less than 'start'.")

    items = await get_media_files(
        filter_dict=final_filters,
        start=start,
        stop=stop,
        sort_field="date_created",
        sort_order=-1
    )
    media =ListOfMediaOut(totalItems=len(items),listOfMedia=items)
    
    return APIResponse(
        status_code=200,
        data=media,
        detail=f"Fetched media with type '{media_type}'"
    )

# -------------------------------------------------------------------
# Get Media by Category
# -------------------------------------------------------------------
@router.get("/by-category/{category}", response_model=APIResponse[ListOfMediaOut])
async def list_media_by_category(
    category: CategoryNameEnum = Path(..., description="The category to filter by"),
    start: Optional[int] = Query(0, description="Start index for pagination"),
    stop: Optional[int] = Query(50, description="Stop index for pagination"),
    filters: Optional[str] = Query(None, description="Optional JSON string of additional MongoDB filter criteria")
):
    """
    Retrieves media files filtered by a specific `category`.
    """
    path_filter = {"category": category}
    
    parsed_filters = {}
    if filters:
        try:
            parsed_filters = json.loads(filters)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON format for 'filters' query parameter."
            )
            
    final_filters = parsed_filters.copy()
    final_filters.update(path_filter)

    if stop < start:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="'stop' cannot be less than 'start'.")

    items = await get_media_files(
        filter_dict=final_filters,
        start=start,
        stop=stop,
        sort_field="date_created",
        sort_order=-1
    )
    
    media =ListOfMediaOut(totalItems=len(items),listOfMedia=items)
    
    return APIResponse(
        status_code=200,
        data=media,
        detail=f"Fetched media with category'{category}'"
    )

# -------------------------------------------------------------------
# List Most Recent Media
# -------------------------------------------------------------------
@router.get("/recent", response_model=APIResponse[ListOfMediaOut])
async def list_most_recent_media(
    start: Optional[int] = Query(0, description="Start index for range-based pagination"),
    stop: Optional[int] = Query(50, description="Stop index for range-based pagination"),
    filters: Optional[str] = Query(None, description="Optional JSON string of MongoDB filter criteria")
):
    """
    Retrieves a list of the most recent media, sorted by `date_created` descending.
    """
    parsed_filters = {}
    if filters:
        try:
            parsed_filters = json.loads(filters)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON format for 'filters' query parameter."
            )

    if stop < start:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="'stop' cannot be less than 'start'.")

    items = await get_media_files(
        filter_dict=parsed_filters,
        start=start or 0,
        stop=stop or 50,
        sort_field="date_created",
        sort_order=-1  # descending
    )

    detail_msg = f"Fetched media {start} to {stop} sorted by most recent"
    media =ListOfMediaOut(totalItems=len(items),listOfMedia=items)
    
    return APIResponse(
        status_code=200,
        data=media,
        detail=detail_msg
    )

# -------------------------------------------------------------------
# List All Media (Root Endpoint)
# -------------------------------------------------------------------
@router.get("/", response_model=APIResponse[ListOfMediaOut])
async def list_media(
    start: Optional[int] = Query(0, description="Start index for range-based pagination"),
    stop: Optional[int] = Query(100, description="Stop index for range-based pagination"),
    filters: Optional[str] = Query(None, description="Optional JSON string of MongoDB filter criteria")
):
    """
    Retrieves a list of Media files with pagination and optional filtering.
    """
    parsed_filters = {}
    if filters:
        try:
            parsed_filters = json.loads(filters)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON format for 'filters' query parameter."
            )

    # Determine Pagination
    if start is not None or stop is not None:
        if start is None or stop is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Both 'start' and 'stop' must be provided together.")
        if stop < start:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="'stop' cannot be less than 'start'.")
        
        items = await get_media_files(filter_dict=parsed_filters, start=start, stop=stop)
        detail_msg = "Fetched media successfully"
    else:
        items = await get_media_files(filter_dict=parsed_filters, start=0, stop=100)
        detail_msg = "Fetched first 100 media records successfully"
        
    if parsed_filters:
        detail_msg += " (with additional filters applied)"
    media =ListOfMediaOut(totalItems=len(items),listOfMedia=items)
    
    return APIResponse(status_code=200, data=media, detail=detail_msg)

# -------------------------------------------------------------------
# Retrieve a single Media Item
# -------------------------------------------------------------------
@router.get("/{id}", response_model=APIResponse[MediaOut])
async def get_media_by_id(
    id: str = Path(..., description="Media ID (UUID or ObjectId string)")
):
    """
    Retrieves a single Media item by its ID.
    """
    # Depending on your DB schema, you might need to convert id to ObjectId here,
    # or if you store UUIDs as strings, this is fine.
    # Assuming standard _id lookup:
    from bson import ObjectId, errors
    
    query = {}
    # specific check if your IDs are ObjectIds or Strings. 
    # If uncertain, we can try both or just pass strict string if using UUIDs.
    try:
        if ObjectId.is_valid(id):
             query = {"_id": ObjectId(id)}
        else:
             query = {"_id": id} # Fallback for UUIDs stored as strings
    except:
         query = {"_id": id}

    item = await get_media(filter_dict=query)
    
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Media item not found")
            
    return APIResponse(status_code=200, data=item, detail="Media item fetched")


