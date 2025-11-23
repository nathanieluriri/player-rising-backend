
from schemas.blog import BlogOutLessDetailUserVersion, ListOfBlogs
from schemas.imports import SearchQuery
from sub_app1.repository.blog import search_blogs_repo


async def search_blogs_service(query_params: SearchQuery):

    # Build a flexible MongoDB find() filter
    filters = {}

    # Case-insensitive regex filters
    if query_params.title:
        filters["title"] = {"$regex": query_params.title, "$options": "i"}

    if query_params.author:
        filters["author.name"] = {"$regex": query_params.author, "$options": "i"}

    filters["state"] = "published"

    # Pagination values
    skip = query_params.start
    limit = query_params.stop

    # Call repo (repo must expose find-based search)
    results = await search_blogs_repo(filters, skip=skip, limit=limit)

    return ListOfBlogs(
        totalItems=len(results),
        blogs=[
            BlogOutLessDetailUserVersion.model_validate(blog)
            for blog in results
        ]
    )
