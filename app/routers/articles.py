from fastapi import APIRouter, File, UploadFile, Form, Header, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timezone
from google.cloud import firestore

from fastapi.responses import JSONResponse
from ..firebase import db
from ..models import ArticleOut, generate_slug
from ..utils import upload_file_to_storage
from google.cloud.firestore_v1 import Increment
from google.cloud.firestore_v1.base_document import DocumentSnapshot

router = APIRouter()

ARTICLES_COLLECTION = "articles"


def convert_firestore_timestamp(timestamp):
    """Convert Firestore timestamp to regular datetime"""
    if hasattr(timestamp, 'isoformat'):
        # If it's already a datetime-like object
        return timestamp
    elif hasattr(timestamp, 'timestamp'):
        # Convert to datetime
        return timestamp
    return timestamp


def prepare_article_data(doc: DocumentSnapshot):
    """Prepare article data for response, converting timestamps"""
    data = doc.to_dict()
    data["id"] = doc.id
    
    # Ensure all required fields are present
    if "author_id" not in data:
        data["author_id"] = "anonymous"
    if "comments_count" not in data:
        data["comments_count"] = 0
    if "likes_count" not in data:
        data["likes_count"] = 0
    if "shares_count" not in data:
        data["shares_count"] = 0
    if "media_urls" not in data:
        data["media_urls"] = []
    if "tags" not in data:
        data["tags"] = []
    if "keywords" not in data:
        data["keywords"] = []
    
    # Convert Firestore timestamps to regular datetime
    if "created_at" in data:
        data["created_at"] = convert_firestore_timestamp(data["created_at"])
    if "updated_at" in data:
        data["updated_at"] = convert_firestore_timestamp(data["updated_at"])
    
    return data


@router.post("/", response_model=ArticleOut)
async def create_article(
    title: str = Form(...), 
    content: str = Form(...), 
    tags: Optional[str] = Form(""), 
    meta_title: Optional[str] = Form(None), 
    meta_description: Optional[str] = Form(None), 
    keywords: Optional[str] = Form(""), 
    thumbnail: Optional[UploadFile] = File(None), 
    media: Optional[List[UploadFile]] = File(None)
):
    # Use "ViKay" as default author_id since we removed auth
    author_id = "ViKay"
    tags_list = [t.strip() for t in tags.split(",")] if tags else []
    keywords_list = [k.strip() for k in keywords.split(",")] if keywords else []

    thumbnail_url = upload_file_to_storage(thumbnail, "thumbnails") if thumbnail else None
    media_urls = [upload_file_to_storage(f, "media") for f in media] if media else []

    now = datetime.now(timezone.utc)
    slug = generate_slug(title)
    doc_ref = db.collection(ARTICLES_COLLECTION).document(slug)
    article_data = {
        "id": slug,
        "slug": slug,
        "title": title,
        "content": content,
        "author_id": author_id,
        "thumbnail_url": thumbnail_url,
        "media_urls": media_urls,
        "tags": tags_list,
        "meta_title": meta_title or title,
        "meta_description": meta_description or content[:150],
        "keywords": keywords_list,
        "created_at": now,
        "updated_at": now,
        "likes_count": 0,
        "comments_count": 0,
        "shares_count": 0
    }
    doc_ref.set(article_data)
    doc = doc_ref.get()
    if doc.exists:
        data = prepare_article_data(doc)
        return ArticleOut(**data)
    else:
        raise HTTPException(status_code=500, detail="Failed to create article")


@router.get("/{slug}", response_model=ArticleOut)
async def get_article(slug: str):
    doc = db.collection(ARTICLES_COLLECTION).document(slug).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Article not found")
    
    data = prepare_article_data(doc)
    
    # Convert to ArticleOut model
    article = ArticleOut(**data)
    
    # You can add share data to the response if needed
    # For now, just return the article
    return article


@router.get("/", response_model=List[ArticleOut])
def list_articles( 
    q: Optional[str] = Query(None), 
    page_size: int = Query(10, ge=1, le=100), 
    page_token: Optional[str] = Query(None)
):
    # FIXED: Use firestore.Query directly
    col = db.collection(ARTICLES_COLLECTION).order_by("created_at", direction=firestore.Query.DESCENDING)
    
    if q:
        snapshot = col.limit(100).stream()
        results = []
        for s in snapshot:
            d = s.to_dict()
            match = q.lower() in d.get("title", "").lower() or any(q.lower() in t.lower() for t in d.get("tags", []))

            if match:
                data = prepare_article_data(s)
                results.append(ArticleOut(**data))
        return results[:page_size]
    
    if page_token:
        try:
            last_doc = db.collection(ARTICLES_COLLECTION).document(page_token).get()
            if not last_doc.exists:
                raise HTTPException(status_code=400, detail="Invalid page_token")
            query = col.start_after({"created_at": last_doc.to_dict()["created_at"]}).limit(page_size)
        except Exception:
            query = col.limit(page_size)
    else:
        query = col.limit(page_size)
    
    articles = []
    for doc in query.stream():
        data = prepare_article_data(doc)
        articles.append(ArticleOut(**data))
    
    return articles


@router.put("/{article_id}", response_model=ArticleOut)
async def update_article(
    article_id: str, 
    title: Optional[str] = Form(None), 
    content: Optional[str] = Form(None), 
    tags: Optional[str] = Form(None), 
    thumbnail: Optional[UploadFile] = File(None), 
    media: Optional[List[UploadFile]] = File(None)
):
    # Removed auth requirement
    doc_ref = db.collection(ARTICLES_COLLECTION).document(article_id)
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Article not found")
    
    updates = {}
    if title: 
        updates["title"] = title
    if content: 
        updates["content"] = content
    if tags: 
        updates["tags"] = [t.strip() for t in tags.split(",")]
    if thumbnail: 
        updates["thumbnail_url"] = upload_file_to_storage(thumbnail, "thumbnails")
    if media:
        data = doc.to_dict()
        media_list = data.get("media_urls", [])
        media_list += [upload_file_to_storage(f, "media") for f in media]
        updates["media_urls"] = media_list
    
    updates["updated_at"] = datetime.now(timezone.utc)
    doc_ref.update(updates)
    
    updated_doc = doc_ref.get()
    data = prepare_article_data(updated_doc)
    
    return ArticleOut(**data)


@router.delete("/{article_id}")
def delete_article(article_id: str):
    # Removed auth requirement
    doc_ref = db.collection(ARTICLES_COLLECTION).document(article_id)
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Article not found")
    
    doc_ref.delete()
    return {"ok": True, "deleted": article_id}