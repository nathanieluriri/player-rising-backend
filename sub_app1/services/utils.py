BLOG_TYPE_MAP = {
    "hero-section": {"blogType": "hero section"},
    "about-section": {"blogType": "about section"},
    "footer-section": {"blogType": "footer section"},
    "sidebar-section": {"blogType": "sidebar section"},
}
def get_path_filter(blog_type):
    try:
        return BLOG_TYPE_MAP[blog_type.value]
    except KeyError:
        raise ValueError(f"Unsupported blog_type: {blog_type.value!r}")