from typing import Optional


BLOG_TYPE_MAP = {
    "hero-section": {"blogType": "hero section"},
    "editors-pick": {"blogType":  "editors pick"},
    "featured": {"blogType": "featured story"},
    "normal": {"blogType": "normal"},
}
def get_path_filter(blog_type):
    try:
        return BLOG_TYPE_MAP[blog_type.value]
    except KeyError:
        raise ValueError(f"Unsupported blog_type: {blog_type.value!r}")
    
    
SORT_MAP = {
    "newest": {"sort_field":"date_created", "sort_order":-1},       # newest
    "oldest": {"sort_field":"date_created", "sort_order": 1},         # oldest
    "mostRecentlyUpdated":  {"sort_field":"last_updated", "sort_order":-1},     # most recently updated
    "leastRecentlyUpdated":  {"sort_field":"last_updated", "sort_order": 1},         # least recently updated
    "latestPublished": {"sort_field":"publishDate", "sort_order": -1},    # latest published
    "earliestPublished": {"sort_field":"publishDate", "sort_order": 1},    # earliest published
}


def get_sort(sort_param: Optional[str]):
    if sort_param is None:
        return None

    try:
        return SORT_MAP[sort_param]
    except KeyError:
        raise ValueError(f"Unsupported sort option: {sort_param!r}")
