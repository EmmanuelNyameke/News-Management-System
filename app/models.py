import re
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


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
    thumbnail_url: Optional[str]
    media_urls: List[str]
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    likes_count: int
    comments_count: int
    shares_count: int
    meta_title: Optional[str]
    meta_description: Optional[str]
    keywords: List[str]


class CommentIn(BaseModel):
    text: str


class CommentOut(BaseModel):
    id: str
    user_id: str
    text: str
    created_at: datetime