from enum import Enum


class BlogType(str,Enum):
    editors_pick= "editors-pick"
    featured_story = "featured"
    hero_section="hero-section"
    normal="normal"
    


class SortType(str,Enum):
    newest= "newest"
    oldest = "oldest"
    mostRecentlyUpdated="mostRecentlyUpdated"
    leastRecentlyUpdated="leastRecentlyUpdated"
    latestPublished="latestPublished"
    earliestPublished="earliestPublished"
    
    
