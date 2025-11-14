# ============================================================================
# BLOG SERVICE
# ============================================================================
# This file was auto-generated on: 2025-11-14 11:54:30 WAT
# It contains  asynchrounous functions that make use of the repo functions 
# 
# ============================================================================

from bson import ObjectId
from fastapi import HTTPException
from typing import List

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


async def retrieve_blogs(start=0,stop=100) -> List[BlogOut]:
    """Retrieves BlogOut Objects in a list

    Returns:
        _type_: BlogOut
    """
    return await get_blogs(start=start,stop=stop)


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