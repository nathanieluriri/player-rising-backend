
# Articles API Documentation

This API provides endpoints for user operations and fetching blogs/articles. It supports filtering, pagination, and retrieving individual blog content.

## Base URL

```
/api/v1
```

---

## Table of Contents

1. [Articles & Blogs](#articles--blogs)

   * [List All Categories](#list-all-categories)
   * [List Blogs By Blog Type](#list-blogs-by-blog-type)
   * [List Blogs By Category Slug](#list-blogs-by-category-slug)
   * [List Blogs By Category Name](#list-blogs-by-category-name)
   * [List Blogs By Author Name](#list-blogs-by-author-name)
   * [List Most Recent Blogs](#list-most-recent-blogs)
   * [List All Blogs](#list-all-blogs)
   * [Get Blog By ID](#get-blog-by-id)

2. [User Routes](#user-routes)

   * *(You can add your user-related endpoints here)*

---

## Articles & Blogs

### List All Categories

```
GET /articles/content/categories
```

**Description:** Retrieves a list of all available blog categories and their slugs.

**Response:**

* 200: `APIResponse[List[Category]]`

```json
{
  "status_code": 200,
  "data": [
    {
      "name": "Manchester United",
      "slug": "manchester-united"
    }
  ],
  "detail": "Categories retrieved successfully."
}
```

---

### List Blogs By Blog Type

```
GET /articles/content/by-blog-type/{blog_type}
```

**Parameters:**

| Name      | In    | Type   | Required | Description                               |
| --------- | ----- | ------ | -------- | ----------------------------------------- |
| blog_type | path  | string | yes      | The type of blog to filter by             |
| start     | query | int    | no       | Start index for pagination (default: 0)   |
| stop      | query | int    | no       | Stop index for pagination (default: 50)   |
| filters   | query | string | no       | JSON string of additional filter criteria |

**Response:**

* 200: `APIResponse[List[BlogOut]]`
* 422: `HTTPValidationError`

---

### List Blogs By Category Slug

```
GET /articles/content/by-category-slug/{slug}
```

**Parameters:**

| Name    | In    | Type   | Required | Description                    |
| ------- | ----- | ------ | -------- | ------------------------------ |
| slug    | path  | string | yes      | Category slug to filter        |
| start   | query | int    | no       | Start index (default: 0)       |
| stop    | query | int    | no       | Stop index (default: 50)       |
| filters | query | string | no       | JSON string of filter criteria |

**Response:** Same as [List Blogs By Blog Type](#list-blogs-by-blog-type)

---

### List Blogs By Category Name

```
GET /articles/content/by-category-name/{name}
```

**Parameters:** Same as **By Category Slug**, but `name` is the category name.

---

### List Blogs By Author Name

```
GET /articles/content/by-author-name
```

**Parameters:**

| Name        | In    | Type   | Required | Description                  |
| ----------- | ----- | ------ | -------- | ---------------------------- |
| author_name | query | string | yes      | Exact match of author's name |
| start       | query | int    | no       | Start index (default: 0)     |
| stop        | query | int    | no       | Stop index (default: 50)     |
| filters     | query | string | no       | Optional JSON filters        |

---

### List Most Recent Blogs

```
GET /articles/content/recent
```

Supports optional filtering and pagination.

---

### List All Blogs

```
GET /articles/content/
```

Supports pagination (`start`, `stop`) and optional filtering.

---

### Get Blog By ID

```
GET /articles/content/{id}
```

**Parameters:**

| Name | In   | Type   | Required | Description         |
| ---- | ---- | ------ | -------- | ------------------- |
| id   | path | string | yes      | Blog ID to retrieve |

---
  

## Response Schemas

* `APIResponse[BlogOut]` – Single blog
* `APIResponse[List[BlogOut]]` – List of blogs
* `APIResponse[List[Category]]` – List of categories
* `HTTPValidationError` – Validation errors
* `BlogOut` – Detailed blog output (title, author, category, slug, feature image, pages, body blocks)
* `Category` – Blog category schema

 