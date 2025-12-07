import re
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from typing import Any


def generate_slug(title: str) -> str:
    slug = re.sub(r'[^a-zA-Z0-9]+', '-', title.lower()).strip('-')
    return slug


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