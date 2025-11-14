
import time
from fastapi import APIRouter, Body, HTTPException, Query, Path, status
from typing import List, Optional
import json
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
# List Blogs (with pagination and filtering)
# ------------------------------
@router.get("/", response_model=APIResponse[List[BlogOut]])
async def list_blogs(
    start: Optional[int] = Query(0, description="Start index for range-based pagination"),
    stop: Optional[int] = Query(100, description="Stop index for range-based pagination"),
    page_number: Optional[int] = Query(0, description="Page number for page-based pagination (0-indexed)"),
    # New: Filter parameter expects a JSON string
    filters: Optional[str] = Query(None, description="Optional JSON string of MongoDB filter criteria (e.g., '{\"field\": \"value\"}')")
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

    # Case 2: Use page_number if provided
    elif page_number is not None:
        if page_number < 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="'page_number' cannot be negative.")
        
        start_index = page_number * PAGE_SIZE
        stop_index = start_index + PAGE_SIZE
        # Pass filters to the service layer
        items = await retrieve_blogs(filters=parsed_filters, start=start_index, stop=stop_index)
        return APIResponse(status_code=200, data=items, detail=f"Fetched page {page_number} successfully")

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
    payload: BlogBase = Body(
        openapi_examples={
            "Create_Full_Blog_With_Pagination": {
                "summary": "Create a full multi-page blog article",
                "description": (
                    "This example shows creating a fully detailed blog entry, including "
                    "pagination for multi-page articles."
                ),
                "value": {
                    "title": "The Rise of Quantum Computing",
                    "author": {
                        "name": "Alice Quantum",
                        "avatarUrl": "https://cdn.example.com/avatars/alice.png",
                        "affiliation": "Quantum Labs Research"
                    },
                    "publishDate": "2025-01-04T10:32:00Z",
                    "category": {
                        "name": "Quantum Technology",
                        "slug": "quantum-technology"
                    },
                    "featureImage": {
                        "url": "https://cdn.example.com/images/quantum-feature.jpg",
                        "altText": "Quantum computer room",
                        "credit": "Photo by Quantum Labs"
                    },
                    "pagination": {
                        "currentPage": 1,
                        "totalPages": 4,
                        "nextPageUrl": "/blog/quantum-computing?page=2",
                        "prevPageUrl": None
                    },
                    "currentPageBody": [
                        {
                            "type": "text",
                            "content": "Quantum computing represents a new paradigm in computation..."
                        },
                        {
                            "type": "image",
                            "url": "https://cdn.example.com/images/quantum-chip.png",
                            "altText": "Quantum processor chip",
                            "caption": "A close-up of a quantum processor."
                        },
                        {
                            "type": "quote",
                            "text": "Quantum computing will transform industries within the decade."
                        },
                        { "type": "divider" }
                    ]
                },
            },

            "Create_Standard_Blog_No_Pagination": {
                "summary": "Create a single-page blog article",
                "description": (
                    "This example demonstrates creating a simple blog article without pagination. "
                    "Most blog posts will follow this structure."
                ),
                "value": {
                    "title": "Understanding Machine Learning Basics",
                    "author": {
                        "name": "John Doe",
                        "avatarUrl": "https://cdn.example.com/avatars/john.png",
                        "affiliation": "ML Academy"
                    },
                    "publishDate": "2025-01-10T09:00:00Z",
                    "category": {
                        "name": "Machine Learning",
                        "slug": "machine-learning"
                    },
                    "featureImage": {
                        "url": "https://cdn.example.com/images/ml-feature.jpg",
                        "altText": "Machine learning visual",
                        "credit": "Image by ML Academy"
                    },
                    "currentPageBody": [
                        {
                            "type": "text",
                            "content": "Machine learning is a subset of artificial intelligence..."
                        },
                        {
                            "type": "image",
                            "url": "https://cdn.example.com/images/ml-model.png",
                            "altText": "ML model diagram",
                            "caption": "Diagram showing a simple ML model."
                        }
                    ]
                }
            }
        }
    )
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
    id: str = Path(..., description="ID of the blog to update"),
    payload: BlogUpdate = Body(
        openapi_examples={
            "Full_Update_With_Pagination": {
                "summary": "Full blog update including pagination",
                "description": (
                    "Comprehensive update example modifying title, author, category, "
                    "feature image, pagination, and page body.\n\n"
                    "⚠️ Pagination is optional but included here."
                ),
                "value": {
                    "title": "AI in 2025: What’s New?",
                    "author": {
                        "name": "John Smith",
                        "avatarUrl": "https://cdn.example.com/avatars/john.png",
                        "affiliation": "FutureTech Journal"
                    },
                    "category": {
                        "name": "Technology",
                        "slug": "technology"
                    },
                    "featureImage": {
                        "url": "https://cdn.example.com/images/ai2025.jpg",
                        "altText": "Futuristic AI concept art",
                        "credit": "Image by TechVision"
                    },
                    "pagination": {
                        "currentPage": 1,
                        "totalPages": 5,
                        "nextPageUrl": "/blog/ai-2025?page=2",
                        "prevPageUrl": None
                    },
                    "currentPageBody": [
                        {
                            "type": "text",
                            "content": "Artificial Intelligence continues to evolve rapidly in 2025..."
                        },
                        {
                            "type": "quote",
                            "text": "AI has become a partner rather than a tool."
                        },
                        {
                            "type": "divider"
                        }
                    ],
                    "last_updated": int(time.time())
                }
            },

            "Minimal_Update_No_Pagination": {
                "summary": "Partial blog update without pagination",
                "description": (
                    "A minimal example updating only title, category, and body content. "
                    "Pagination is omitted because it is optional."
                ),
                "value": {
                    "title": "Updated: Understanding Neural Networks",
                    "category": {
                        "name": "Machine Learning",
                        "slug": "machine-learning"
                    },
                    "currentPageBody": [
                        {
                            "type": "text",
                            "content": "Neural networks are inspired by the structure of the human brain..."
                        },
                        {
                            "type": "image",
                            "url": "https://cdn.example.com/images/neural-diagram.png",
                            "altText": "Neural network diagram",
                            "caption": "A simple neural network structure."
                        }
                    ],
                    "last_updated": int(time.time())
                }
            }
        }
    ),
):
    """
    Updates an existing Blog by its ID.
    Assumes the service layer handles partial updates (e.g., ignores None fields in payload).
    """
    updated_item = await update_blog_by_id(id=id, data=payload)
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
