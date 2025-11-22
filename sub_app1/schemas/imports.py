from enum import Enum


class BlogType(str,Enum):
    editors_pick= "editors-pick"
    featured_story = "featured-story"
    hero_section="hero-section"
    normal="normal"
    
