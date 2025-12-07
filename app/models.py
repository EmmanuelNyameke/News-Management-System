import re
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from typing import Any
from urllib.parse import quote


def generate_slug(title: str) -> str:
    slug = re.sub(r'[^a-zA-Z0-9]+', '-', title.lower()).strip('-')
    return slug


def generate_og_tags(article_data: dict) -> dict:
    """Generate Open Graph meta tags for article sharing"""
    # Extract data from article
    title = article_data.get("meta_title") or article_data.get("title", "")
    description = article_data.get("meta_description") or article_data.get("content", "")
    thumbnail_url = article_data.get("thumbnail_url") or "https://vikayblog.com/vikayblog_app_icon.png"
    article_id = article_data.get("id", "")
    
    # Limit description length for social media
    if description:
        description = description[:150] + "..." if len(description) > 150 else description
    
    og_tags = {
        "og_title": title,
        "og_description": description,
        "og_image": thumbnail_url,
        "og_url": f"https://vikayblog.com/articles/{article_id}",
        "twitter_card": "summary_large_image",
        "twitter_title": title,
        "twitter_description": description,
        "twitter_image": thumbnail_url,
    }
    return og_tags


def get_share_urls(article_data: dict) -> dict:
    """Generate share URLs for different social media platforms"""
    article_id = article_data.get("id", "")
    title = article_data.get("title", "")
    description = article_data.get("content", "")[:100]
    thumbnail_url = article_data.get("thumbnail_url") or "https://vikayblog.com/vikayblog_app_icon.png"
    base_url = f"https://vikayblog.com/articles/{article_id}"
    
    # URL encode the parameters
    encoded_title = quote(title)
    encoded_description = quote(description)
    encoded_url = quote(base_url)
    encoded_image = quote(thumbnail_url)
    
    share_urls = {
        "twitter": f"https://twitter.com/intent/tweet?text={encoded_title}&url={encoded_url}",
        "facebook": f"https://www.facebook.com/sharer/sharer.php?u={encoded_url}&quote={encoded_title}",
        "linkedin": f"https://www.linkedin.com/sharing/share-offsite/?url={encoded_url}&title={encoded_title}&summary={encoded_description}",
        "whatsapp": f"https://wa.me/?text={encoded_title}%20-%20{encoded_description}...%20{encoded_url}",
        "telegram": f"https://t.me/share/url?url={encoded_url}&text={encoded_title}%20-%20{encoded_description}...",
        "email": f"mailto:?subject={encoded_title}&body={encoded_title}%0A%0A{encoded_description}...%0A%0ARead%20more:%20{encoded_url}"
    }
    
    return share_urls


class ArticleIn(BaseModel):
    title: str
    content: str
    tags: List[str] = []
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    keywords: List[str] = []


class ArticleOut(BaseModel):
    id: str
    slug: str
    title: str
    content: str
    author_id: str
    thumbnail_url: Optional[str] = None
    media_urls: List[str] = []
    tags: List[str] = []
    created_at: datetime
    updated_at: datetime
    likes_count: int = 0
    comments_count: int = 0
    shares_count: int = 0
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    keywords: List[str] = []

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if hasattr(v, 'isoformat') else str(v)
        }
        
    def get_og_tags(self) -> dict:
        """Get Open Graph tags for this article"""
        return generate_og_tags(self.dict())
    
    def get_share_urls(self) -> dict:
        """Get share URLs for this article"""
        return get_share_urls(self.dict())


class CommentIn(BaseModel):
    text: str


class CommentOut(BaseModel):
    id: str
    user_id: str
    text: str
    created_at: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if hasattr(v, 'isoformat') else str(v)
        }