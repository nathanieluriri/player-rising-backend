
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
    payload: BlogBase = Body( # Using string "BlogBase" as placeholder
        openapi_examples={

            # ----- 1. NEW: Create with Rich Styling & Alignment -----
            "Create_With_Rich_Styling_And_Alignment": {
                "summary": "Create a blog with rich text and alignment",
                "description": (
                    "This example shows a single-page blog using headings, text alignment, "
                    "and styled (bold, italic) rich text content."
                ),
                "value": {
                    "title": "My Styled Article",
                    "author": {
                        "name": "Jane Designer",
                        "avatarUrl": "https://cdn.example.com/avatars/jane.png",
                        "affiliation": "Design Weekly"
                    },
                    "category": {
                        "name": "Juventus",
                        "slug": "juventus"
                    },
                    "featureImage": {
                        "url": "https://cdn.example.com/images/styled-feature.jpg",
                        "altText": "Abstract design",
                        "credit": "Photo by Jane"
                    },
                    "currentPageBody": [
                        {
                            "type": "heading",
                            "level": 1,
                            "align": "center",
                            "content": [
                                {"type": "text", "text": "This is a Centered Heading", "styles": {}}
                            ]
                        },
                        {
                            "type": "paragraph",
                            "align": "left",
                            "content": [
                                {"type": "text", "text": "This is ", "styles": {}},
                                {"type": "text", "text": "bold text", "styles": {"bold": True}},
                                {"type": "text", "text": ", this is ", "styles": {}},
                                {"type": "text", "text": "italic text", "styles": {"italic": True}},
                                {"type": "text", "text": ", and this is ", "styles": {}},
                                {"type": "text", "text": "bold and italic", "styles": {"bold": True, "italic": True}},
                                {"type": "text", "text": ".", "styles": {}}
                            ]
                        },
                        {
                            "type": "image",
                            "align": "center",
                            "url": "https://cdn.example.com/images/centered-image.png",
                            "altText": "A centered image",
                            "caption": "This image is centered.",
                            "previewWidth": 600,
                            "previewHeight": 400
                        },
                        {
                            "type": "quote",
                            "align": "right",
                            "content": [
                                {"type": "text", "text": "A quote, aligned to the right.", "styles": {"italic": True}}
                            ]
                        }
                    ]
                }
            },

            # ----- 2. Full multi-page blog (UPDATED) -----
            "Create_Full_Blog_With_Multiple_Pages": {
                "summary": "Create a full multi-page blog article",
                "description": (
                    "This example demonstrates creating a detailed blog entry with multiple pages, "
                    "using the new rich text models."
                ),
                "value": {
                    "title": "The Rise of Quantum Computing",
                    "author": {
                        "name": "Alice Quantum",
                        "avatarUrl": "https://cdn.example.com/avatars/alice.png",
                        "affiliation": "Quantum Labs Research"
                    },
                    "category": {
                        "name": "Juventus",
                        "slug": "juventus"
                    },
                    "featureImage": {
                        "url": "https://cdn.example.com/images/quantum-feature.jpg",
                        "altText": "Quantum computer room",
                        "credit": "Photo by Quantum Labs"
                    },
                    "pages": [
                        {
                            "pageNumber": 1,
                            "pageBody": [
                                {
                                    "type": "paragraph",
                                    "content": [
                                        {"type": "text", "text": "Quantum computing represents a new paradigm...", "styles": {}}
                                    ]
                                },
                                {
                                    "type": "image",
                                    "url": "https://cdn.example.com/images/quantum-chip.png",
                                    "altText": "Quantum processor chip",
                                    "caption": "Close-up of a quantum processor.",
                                    "previewWidth": 500,
                                    "previewHeight": 300
                                },
                                {
                                    "type": "quote",
                                    "content": [
                                        {"type": "text", "text": "Quantum computing will transform industries.", "styles": {"italic": True}}
                                    ]
                                },
                                {
                                    "type": "divider"
                                }
                            ]
                        },
                        {
                            "pageNumber": 2,
                            "pageBody": [
                                {
                                    "type": "paragraph",
                                    "content": [
                                        {"type": "text", "text": "The second page continues the exploration of quantum computing.", "styles": {}}
                                    ]
                                }
                            ]
                        }
                    ]
                }
            },

            # ----- 3. Standard single-page blog (UPDATED) -----
            "Create_Standard_Blog_Without_Multiple_Pages": {
                "summary": "Create a single-page blog article",
                "description": "Simple blog article without multiple pages, using new rich text models.",
                "value": {
                    "title": "Understanding Machine Learning Basics",
                    "author": {
                        "name": "John Doe",
                        "avatarUrl": "https://cdn.example.com/avatars/john.png",
                        "affiliation": "ML Academy"
                    },
                    "category": {
                        "name": "Juventus",
                        "slug": "juventus"
                    },
                    "featureImage": {
                        "url": "https://cdn.example.com/images/ml-feature.jpg",
                        "altText": "Machine learning visual",
                        "credit": "Image by ML Academy"
                    },
                    "currentPageBody": [
                        {
                            "type": "paragraph",
                            "content": [
                                {"type": "text", "text": "Machine learning is a subset of AI...", "styles": {}}
                            ]
                        },
                        {
                            "type": "image",
                            "url": "https://cdn.example.com/images/ml-model.png",
                            "altText": "ML model diagram",
                            "caption": "Diagram showing a simple ML model.",
                            "previewWidth": 450,
                            "previewHeight": 250
                        }
                    ]
                }
            },

            # ----- 4. Minimal single-page blog (UPDATED) -----
            "Create_Minimal_Single_Page_Blog": {
                "summary": "Minimal single-page blog",
                "description": "A small blog with only title, category, and one paragraph.",
                "value": {
                    "title": "Intro to Neural Networks",
                    "author": {
                        "name": "Jane Smith",
                        "avatarUrl": "https://cdn.example.com/avatars/jane.png",
                        "affiliation": "AI Academy"
                    },
                    "category": {
                        "name": "Juventus",
                        "slug": "juventus"
                    },
                    "featureImage": {
                        "url": "https://cdn.example.com/images/nn-feature.jpg",
                        "altText": "Neural network visual",
                        "credit": "AI Academy"
                    },
                    "currentPageBody": [
                        {
                            "type": "paragraph",
                            "content": [
                                {"type": "text", "text": "Neural networks mimic the human brain for pattern recognition.", "styles": {}}
                            ]
                        }
                    ]
                }
            },

            # ----- 5. Multi-page blog with multiple pages (UPDATED) -----
            "Create_Multi_Page_Blog_Multiple_Pages": {
                "summary": "Multi-page blog with multiple pages",
                "description": "Shows a blog split across three pages with mixed content types.",
                "value": {
                    "title": "AI and Society in 2030",
                    "author": {
                        "name": "Dr. Alan Turing",
                        "avatarUrl": "https://cdn.example.com/avatars/alan.png",
                        "affiliation": "Future AI Institute"
                    },
                    "category": {
                        "name": "Juventus",
                        "slug": "juventus"
                    },
                    "featureImage": {
                        "url": "https://cdn.example.com/images/ai-society.jpg",
                        "altText": "AI concept art",
                        "credit": "Future AI Institute"
                    },
                    "pages": [
                        {
                            "pageNumber": 1,
                            "pageBody": [
                                {"type": "paragraph", "content": [{"type": "text", "text": "Page 1: Introduction to AI impact on society.", "styles": {}}]}
                            ]
                        },
                        {
                            "pageNumber": 2,
                            "pageBody": [
                                {"type": "paragraph", "content": [{"type": "text", "text": "Page 2: Ethical considerations of AI.", "styles": {}}]}
                            ]
                        },
                        {
                            "pageNumber": 3,
                            "pageBody": [
                                {"type": "paragraph", "content": [{"type": "text", "text": "Page 3: Future predictions and summary.", "styles": {}}]}
                            ]
                        }
                    ]
                }
            },

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
    payload: BlogUpdate = Body( # Using string "BlogUpdate" as placeholder
        openapi_examples={

            # ----- 1. Update only the title (No Change) -----
            "Update_Title_Only": {
                "summary": "Update only the blog title",
                "description": "Shows a PATCH request that updates just the title field.",
                "value": {
                    "title": "Updated: AI Revolution 2025",
                }
            },

            # ----- 2. Update author only (No Change) -----
            "Update_Author_Only": {
                "summary": "Update only the author",
                "description": "Updates only the author info without touching other fields.",
                "value": {
                    "author": {
                        "name": "Alice Quantum",
                        "avatarUrl": "https://cdn.example.com/avatars/alice.png",
                        "affiliation": "Quantum Labs Research"
                    },
                }
            },

            # ----- 3. Update category only (No Change) -----
            "Update_Category_Only": {
                "summary": "Update only the category",
                "description": "Patch request modifying only the category of the blog.",
                "value": {
                    "category": {
                        "name": "Juventus",
                        "slug": "juventus"
                    },
                }
            },

            # ----- 4. Update featureImage only (No Change) -----
            "Update_FeatureImage_Only": {
                "summary": "Update only the feature image",
                "description": "Modifies only the feature image.",
                "value": {
                    "featureImage": {
                        "url": "https://cdn.example.com/images/ai2025-new.jpg",
                        "altText": "AI concept art updated",
                        "credit": "Image by TechVision"
                    },
                }
            },

            # ----- 5. NEW: Update with Rich Content & Alignment -----
            "Update_With_Rich_Content": {
                "summary": "Update body with rich text and alignment",
                "description": "Shows a PATCH request using heading, alignment, and styled text, matching the new API models.",
                "value": {
                    "currentPageBody": [
                        {
                            "type": "heading",
                            "level": 1,
                            "align": "center",
                            "content": [
                                {"type": "text", "text": "This is a Centered Heading", "styles": {}}
                            ]
                        },
                        {
                            "type": "paragraph",
                            "align": "left",
                            "content": [
                                {"type": "text", "text": "This is ", "styles": {}},
                                {"type": "text", "text": "bold text", "styles": {"bold": True}},
                                {"type": "text", "text": " and this is ", "styles": {}},
                                {"type": "text", "text": "italic text.", "styles": {"italic": True}}
                            ]
                        },
                        {
                            "type": "image",
                            "align": "right",
                            "url": "https://cdn.example.com/images/aligned-image.png",
                            "altText": "A right-aligned image",
                            "caption": "This image is aligned to the right.",
                            "previewWidth": 300,
                            "previewHeight": 300
                        }
                    ]
                }
            },

            # ----- 6. Update currentPageBody only (UPDATED) -----
            "Update_CurrentPageBody_Only": {
                "summary": "Update the body of the current page",
                "description": "Updates the content of a single-page blog using the new rich text models.",
                "value": {
                    "currentPageBody": [
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "Neural networks continue to dominate AI research...",
                                    "styles": {}
                                }
                            ]
                        },
                        {
                            "type": "image",
                            "url": "https://cdn.example.com/images/neural-updated.png",
                            "altText": "Updated neural network diagram",
                            "caption": "Updated diagram for clarity.",
                            "previewWidth": 500,
                            "previewHeight": 350
                        }
                    ],
                }
            },

            # ----- 7. Update pages only (multi-page blog) (UPDATED) -----
            "Update_Pages_Only": {
                "summary": "Update multi-page blog content",
                "description": "Updates only the pages array of a multi-page blog, using new content models.",
                "value": {
                    "pages": [
                        {
                            "pageNumber": 1,
                            "pageBody": [
                                {
                                    "type": "paragraph",
                                    "content": [
                                        {
                                            "type": "text",
                                            "text": "Artificial Intelligence evolves rapidly in 2025...",
                                            "styles": {}
                                        }
                                    ]
                                },
                                {
                                    "type": "quote",
                                    "content": [
                                        {
                                            "type": "text",
                                            "text": "AI has become a partner rather than a tool.",
                                            "styles": {}
                                        }
                                    ]
                                }
                            ]
                        },
                        {
                            "pageNumber": 2,
                            "pageBody": [
                                {
                                    "type": "paragraph",
                                    "content": [
                                        {
                                            "type": "text",
                                            "text": "Second page content goes here...",
                                            "styles": {}
                                        }
                                    ]
                                }
                            ]
                        }
                    ],
                }
            },

            # ----- 8. Full update example (UPDATED) -----
            "Full_Update_With_Pagination": {
                "summary": "Full blog update including all fields",
                "description": "Comprehensive example modifying all fields with new body content models.",
                "value": {
                    "title": "AI in 2025: What’s New?",
                    "author": {
                        "name": "John Smith",
                        "avatarUrl": "https://cdn.example.com/avatars/john.png",
                        "affiliation": "FutureTech Journal"
                    },
                    "category": {
                        "name": "Juventus",
                        "slug": "juventus"
                    },
                    "featureImage": {
                        "url": "https://cdn.example.com/images/ai2025.jpg",
                        "altText": "Futuristic AI concept art",
                        "credit": "Image by TechVision"
                    },
                    "pages": [
                        {
                            "pageNumber": 1,
                            "pageBody": [
                                {
                                    "type": "paragraph",
                                    "content": [
                                        {
                                            "type": "text",
                                            "text": "Artificial Intelligence continues to evolve rapidly in 2025...",
                                            "styles": {}
                                        }
                                    ]
                                },
                                {
                                    "type": "quote",
                                    "content": [
                                        {
                                            "type": "text",
                                            "text": "AI has become a partner rather than a tool.",
                                            "styles": {"italic": True}
                                        }
                                    ]
                                },
                                {
                                    "type": "divider"
                                }
                            ]
                        }
                    ],
                }
            },

            # ----- 9. Update blog type only (No Change) -----
            "Update_Blog_Type_Only": {
                "summary": "Update only the blog type",
                "description": "Updates only the Blog_Type without touching other fields.",
                "value": {
                    "blogType": "editors pick"
                }
            },

        }
    ),
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
