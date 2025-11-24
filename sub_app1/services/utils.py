from typing import Optional
import requests
import urllib.parse
from functools import lru_cache
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


@lru_cache(maxsize=100)
def get_club_fanart_url_robust(team_name: str) -> Optional[str]:
    """
    Retrieves a suitable image URL for a given football club name from TheSportsDB API,
    checking multiple fanart and logo fields in a defined priority order.

    Args:
        team_name (str): The name of the football club (e.g., "Liverpool", "Chelsea").

    Returns:
        Optional[str]: The first available image URL based on priority, or None if no image is found.
    """
    # Define the priority of image keys to check (most preferred first)
    IMAGE_PRIORITY = [
        "strFanart3",  # Your primary choice
        "strFanart2",
        "strFanart1",
        "strFanart4",
        "strTeamBadge", # Fallback to the club crest/logo
        "strTeamLogo"   # Another potential logo fallback
    ]
    
    # 1. Define the base API details
    BASE_URL = "https://www.thesportsdb.com/api/v1/json/3/"
    ENDPOINT = "searchteams.php"

    # URL-encode the team name for safe inclusion in the query string
    encoded_team_name = urllib.parse.quote_plus(team_name)

    # 2. Construct the full API URL
    url = f"{BASE_URL}{ENDPOINT}?t={encoded_team_name}"
    
    try:
        # 3. Make the API request
        response = requests.get(url)
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        data = response.json()

        # 4. Parse the JSON response
        if data.get('teams') and len(data['teams']) > 0:
            team_data = data['teams'][0]
            
            # 5. Loop through the priority list and return the first valid URL
            for key in IMAGE_PRIORITY:
                image_url = team_data.get(key)
                # Check if the key exists AND has a value (is not None or an empty string)
                if image_url:
                    print(f"Success: Found image for {team_name} using key: **{key}**")
                    return image_url
            
            # If the loop completes without finding an image
            print(f"Error: Found team '{team_name}', but none of the preferred image keys were available.")
            return None
            
        else:
            print(f"Error: Team '{team_name}' not found in TheSportsDB.")
            return None

    except requests.exceptions.RequestException as err:
        print(f"An error occurred during the API request: {err}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during processing: {e}")
        return None