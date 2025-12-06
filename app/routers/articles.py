from fastapi import APIRouter, File, UploadFile, Form, Header, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timezone

from fastapi.responses import JSONResponse
from ..firebase import db
from ..models import ArticleOut, generate_slug
from ..dependencies import verify_firebase_token
from ..utils import upload_file_to_storage
from google.cloud.firestore_v1 import Increment

router = APIRouter()

ARTICLES_COLLECTION = "articles"


@router.post("/", response_model=ArticleOut)
async def create_article(title: str = Form(...), content: str = Form(...), tags: Optional[str] = Form(""), meta_title: Optional[str] = Form(None), meta_description: Optional[str] = Form(None), keywords: Optional[str] = Form(""), thumbnail: Optional[UploadFile] = File(None), media: Optional[List[UploadFile]] = File(None), authorization: str = Header(...)):
    user = verify_firebase_token(authorization)
    author_id = user["uid"]
    tags_list = [t.strip() for t in tags.split(",")] if tags else []
    keywords = [k.strip() for k in keywords.split(",")] if keywords else []

    thumbnail_url = upload_file_to_storage(thumbnail, "thumbnails") if thumbnail else None
    media_urls = [upload_file_to_storage(f, "media") for f in media] if media else []

    now = datetime.now(timezone.utc)
    slug = generate_slug(title)
    doc_ref = db.collection(ARTICLES_COLLECTION).document(slug)
    article_data = {
        "slug": slug,
        "title": title,
        "content": content,
        "author_id": author_id,
        "thumbnail_url": thumbnail_url,
        "media_urls": media_urls,
        "tags": tags_list,
        "meta_title": meta_title or title,
        "meta_description": meta_description or content[:150],
        "keywords": keywords,
        "created_at": now,
        "updated_at": now,
        "likes_count": 0,
        "Comments_count": 0,
        "shares_count": 0
    }
    doc_ref.set(article_data)
    doc = doc_ref.get().to_dict()
    return ArticleOut(id=slug, **doc)


@router.get("/{slug}", response_model=ArticleOut)
async def get_article(slug: str):
    doc = db.collection(ARTICLES_COLLECTION).document(slug).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Article not found")
    data = doc.to_dict()
    response = JSONResponse(content=data)
    response.headers["Cache-Control"] = "public, max-age=3600"
    return response


@router.get("/", response_model=List[ArticleOut])
def list_articles( q: Optional[str] = Query(None), page_size: int = Query(10, ge=1, le=100), page_token: Optional[str] = Query(None)):
    col = db.collection(ARTICLES_COLLECTION).order_by("created_at", direction=db.Query.DESCENDING)
    if q:
        snapshot = col.limit(100).stream()
        results = []
        for s in snapshot:
            d = s.to_dict()
            match = q.lower() in d.get("title", "").lower() or any(q.lower() in t.lower() for t in d.get("tags", []))

            if match:
                results.append(ArticleOut(id=s.id, **d))
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
    return [ArticleOut(id=d.id, **d.to_dict()) for d in query.stream()]


@router.get("/{article_id}", response_model=ArticleOut)
def get_article(article_id: str):
    doc = db.collection(ARTICLES_COLLECTION).document(article_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Article not found")
    return ArticleOut(id=doc.id, **doc.to_dict())


@router.put("/article_id", response_model=ArticleOut)
async def update_article(article_id: str, title: Optional[str] = Form(None), content: Optional[str] = Form(None), tags: Optional[str] = Form(None), thumbnail: Optional[UploadFile] = File(None), media: Optional[str] = File(None), authorization: str = Header(...)):
    user = verify_firebase_token(authorization)
    uid = user["uid"]
    doc_ref = db.collection(ARTICLES_COLLECTION).document(article_id)
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Article not found")
    data = doc.to_dict()
    if data.get("author_id") != uid:
        raise HTTPException(status_code=403, detail="Only author can update")
    
    updates = {}
    if title: updates["title"] = title
    if content: updates["content"] = content
    if tags: updates["tags"] = [t.strip() for t in tags.split(",")]
    if thumbnail: updates["thumbnail_url"] = upload_file_to_storage(thumbnail, "thumbnails")
    if media:
        media_list = data.get("media_urls", [])
        media_list += [upload_file_to_storage(f, "media") for f in media]
        updates["media_urls"] = media_list
    updates["updated_at"] = datetime.now(timezone.utc)
    doc_ref.update(updates)
    return ArticleOut(id=doc_ref.id, **doc_ref.get().to_dict())

@router.delete("/{article_id}")
def delete_article(article_id: str, authorization: str = Header(...)):
    user = verify_firebase_token(authorization)
    uid = user ["uid"]
    doc_ref = db.collection(ARTICLES_COLLECTION).document(article_id)
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Article not found")
    data = doc.to_dict()
    if data.get("author_id") != uid:
        raise HTTPException(status_code=403, detail="Only author can delete")
    doc_ref.delete()
    return {"ok": True, "deleted": article_id}
