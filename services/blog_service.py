# ============================================================================
# BLOG SERVICE
# ============================================================================
# This file was auto-generated on: 2025-11-14 11:54:30 WAT
# It contains  asynchrounous functions that make use of the repo functions 
# 
# ============================================================================

from bson import ObjectId
from fastapi import HTTPException
from typing import List, Optional

from repositories.blog import (
    create_blog,
    get_blog,
    get_blogs,
    update_blog,
    delete_blog,
)
from schemas.blog import BlogCreate, BlogUpdate, BlogOut


async def add_blog(blog_data: BlogCreate) -> BlogOut:
    """adds an entry of BlogCreate to the database and returns an object

    Returns:
        _type_: BlogOut
    """
    return await create_blog(blog_data)


async def remove_blog(blog_id: str):
    """deletes a field from the database and removes BlogCreateobject 

    Raises:
        HTTPException 400: Invalid blog ID format
        HTTPException 404:  Blog not found
    """
    if not ObjectId.is_valid(blog_id):
        raise HTTPException(status_code=400, detail="Invalid blog ID format")

    filter_dict = {"_id": ObjectId(blog_id)}
    result = await delete_blog(filter_dict)

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Blog not found")
    else: return True


async def retrieve_blog_by_blog_id(id: str) -> BlogOut:
    """Retrieves blog object based specific Id 

    Raises:
        HTTPException 404(not found): if  Blog not found in the db
        HTTPException 400(bad request): if  Invalid blog ID format

    Returns:
        _type_: BlogOut
    """
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid blog ID format")

    filter_dict = {"_id": ObjectId(id)}
    result = await get_blog(filter_dict)

    if not result:
        raise HTTPException(status_code=404, detail="Blog not found")

    return result

async def retrieve_blogs(
    filters: Optional[dict] = None,
    start: int = 0,
    stop: int = 100,
    sort_field: Optional[str] = None,
    sort_order: Optional[int] = None  # 1 for ascending, -1 for descending
) -> List[BlogOut]:
    """
    Retrieves BlogOut objects from the database with optional filtering,
    pagination, and sorting.

    Args:
        filters (dict, optional): MongoDB filter criteria.
        start (int): Start index for pagination.
        stop (int): Stop index for pagination.
        sort_field (str, optional): Field to sort by.
        sort_order (int, optional): 1 for ascending, -1 for descending.

    Returns:
        List[BlogOut]: List of blog objects.
    """
    
    # Case 1: Filters + Sort
    if filters and filters != {"field": "value"} and sort_field and sort_order:
        return await get_blogs(
            filter_dict=filters,
            start=start,
            stop=stop,
            sort_field=sort_field,
            sort_order=sort_order
        )

    # Case 2: Filters only
    elif filters and filters != {"field": "value"}:
        return await get_blogs(
            filter_dict=filters,
            start=start,
            stop=stop
        )

    # Case 3: Sort only
    elif sort_field and sort_order:
        return await get_blogs(
            start=start,
            stop=stop,
            sort_field=sort_field,
            sort_order=sort_order
        )

    # Case 4: No filters or sort
    else:
        return await get_blogs(start=start, stop=stop)


async def update_blog_by_id(blog_id: str, blog_data: BlogUpdate) -> BlogOut:
    """updates an entry of blog in the database

    Raises:
        HTTPException 404(not found): if Blog not found or update failed
        HTTPException 400(not found): Invalid blog ID format

    Returns:
        _type_: BlogOut
    """
    if not ObjectId.is_valid(blog_id):
        raise HTTPException(status_code=400, detail="Invalid blog ID format")

    filter_dict = {"_id": ObjectId(blog_id)}
    result = await update_blog(filter_dict, blog_data)

    if not result:
        raise HTTPException(status_code=404, detail="Blog not found or update failed")

    return result