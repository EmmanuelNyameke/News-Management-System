from fastapi import APIRouter, HTTPException
from ..firebase import db
from google.cloud import firestore
from .articles import ARTICLES_COLLECTION
from google.cloud.firestore_v1 import Increment

router = APIRouter()
LIKES_SUBCOL = "likes"

@router.post("/{article_id}/like")
def like_article(article_id: str):
    # Removed auth requirement
    user_id = "anonymous"  # Default user ID
    article_ref = db.collection(ARTICLES_COLLECTION).document(article_id)
    if not article_ref.get().exists:
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
    
    article_data = article_doc.to_dict()
    
    # Increment share count
    article_ref.update({"shares_count": Increment(1)})
    
    # Return comprehensive share data
    return {
        "shared": True,
        "share_url": f"https://vikayblog.com/article-detail.html?id={article_id}",
        "title": article_data.get("title", "Article"),
        "description": article_data.get("meta_description", article_data.get("content", "")[:150]),
        "image": article_data.get("thumbnail_url", "https://vikayblog.com/vikayblog_app_icon.png")
    }