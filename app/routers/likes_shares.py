from fastapi import APIRouter, HTTPException
from ..firebase import db
from google.cloud import firestore
from .articles import ARTICLES_COLLECTION, prepare_article_data
from google.cloud.firestore_v1 import Increment
from ..models import generate_og_tags, get_share_urls

router = APIRouter()
LIKES_SUBCOL = "likes"


@router.post("/{article_id}/like")
def like_article(article_id: str):
    # Removed auth requirement
    user_id = "ViKay"  # Default user ID
    article_ref = db.collection(ARTICLES_COLLECTION).document(article_id)
    article_doc = article_ref.get()
    
    if not article_doc.exists:
        raise HTTPException(status_code=404, detail="Article not found")
    
    like_ref = article_ref.collection(LIKES_SUBCOL).document(user_id)
    like_doc = like_ref.get()
    
    if like_doc.exists:
        like_ref.delete()
        article_ref.update({"likes_count": Increment(-1)})
        return {"liked": False}
    else:
        like_ref.set({"user_id": user_id, "created_at": firestore.SERVER_TIMESTAMP})
        article_ref.update({"likes_count": Increment(1)})
        return {"liked": True}
    

@router.post("/{article_id}/share")
def share_article(article_id: str):
    article_ref = db.collection(ARTICLES_COLLECTION).document(article_id)
    article_doc = article_ref.get()
    
    if not article_doc.exists:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Update share count
    article_ref.update({"shares_count": Increment(1)})
    
    # Get article data with proper preparation
    article_data = prepare_article_data(article_doc)
    
    # Generate share URLs
    share_url = f"https://vikayblog.com/articles/{article_id}"
    
    # Prepare description from content
    content = article_data.get("content", "")
    description = content[:150] + "..." if len(content) > 150 else content
    
    # Prepare response with rich sharing data
    response_data = {
        "shared": True,
        "share_url": share_url,
        "og_tags": generate_og_tags(article_data),
        "social_urls": get_share_urls(article_data),
        "article_title": article_data.get("title", ""),
        "article_description": description,
        "article_image": article_data.get("thumbnail_url") or "https://vikayblog.com/vikayblog_app_icon.png",
        "article_tags": article_data.get("tags", []),
        "article_author": article_data.get("author_id", "VikayBlog")
    }
    
    return response_data