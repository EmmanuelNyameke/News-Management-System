from fastapi import APIRouter, HTTPException, Header
from ..firebase import db
from ..dependencies import verify_firebase_token
from .articles import ARTICLES_COLLECTION
from google.cloud.firestore_v1 import Increment

router = APIRouter()
LIKES_SUBCOL = "likes"

@router.post("/{article_id}/like")
def like_article(article_id: str, authorization: str = Header(...)):
    user = verify_firebase_token(authorization)
    uid = user["uid"]
    article_ref = db.collection(ARTICLES_COLLECTION).document(article_id)
    if not article_ref.get().exists():
        raise HTTPException(status_code=404, detail="Article not found")
    like_ref = article_ref.collection(LIKES_SUBCOL).document(uid)
    if like_ref.get().exists:
        like_ref.delete()
        article_ref.update({"likes_count": Increment(-1)})
        return {"liked": False}
    else:
        like_ref.set({"user_id": uid, "created_at": db.SERVER_TIMESTAMP})
        article_ref.update({"likes_count": Increment(1)})
        return {"liked": True}
    

@router.post("/{article_id}/share")
def share_article(article_id: str):
    article_ref = db.collection(ARTICLES_COLLECTION).document(article_id)
    if not article_ref.get().exists:
        raise HTTPException(status_code=404, detail="Article not found")
    article_ref.update({"shares_count": Increment(1)})
    share_url = f"https://vikayblog.com/articles/{article_id}"
    return {"shared": True, "share_url": share_url}

