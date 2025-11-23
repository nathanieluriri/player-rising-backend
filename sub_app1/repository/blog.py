
# ============================================================
# Search Blogs (Text + Field Filters)
# ============================================================

from typing import List

from fastapi import HTTPException,status
from core.database import db
from schemas.blog import BlogOutLessDetailUserVersion


async def search_blogs_repo(
    filters: dict,
    skip: int,
    limit: int
) -> List[BlogOutLessDetailUserVersion]:
    """
    Executes a MongoDB find() query for searching blogs.
    Adds pagination, total count, and index numbering to results.
    """
   
    try:
        # 1️⃣ Get total count BEFORE pagination
        total_items = await db.blogs.count_documents(filters)

        # 2️⃣ Apply pagination with find()
        cursor = (
            db.blogs
            .find(filters)
            .skip(skip)
            .limit(limit)
        )

        results = []
        item_index = skip + 1

        async for doc in cursor:
            blog_item = BlogOutLessDetailUserVersion(**doc)
      
            blog_item.itemIndex = item_index
            results.append(blog_item)
            item_index += 1

        return results

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while searching blogs: {str(e)}"
        )

