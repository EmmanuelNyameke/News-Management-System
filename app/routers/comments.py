from fastapi import APIRouter, HTTPException, Header
from typing import List
from datetime import datetime, timezone
from google.cloud import firestore

from .articles import ARTICLES_COLLECTION
from ..firebase import db
from ..models import CommentIn, CommentOut
from ..dependencies import verify_firebase_token
from google.cloud.firestore_v1 import Increment

router = APIRouter()
COMMENTS_SUBCOL = "comments"

@router.post("/{article_id}/comments", response_model=CommentOut)
def post_comment(article_id: str, payload: CommentIn, authorization: str = Header(...)):
    user = verify_firebase_token(authorization)
    uid = user["uid"]
    article_ref = db.collection(ARTICLES_COLLECTION).document(article_id)
    if not article_ref.get().exists:
        raise HTTPException(status_code=404, detail="Article not found")
    comment_ref = article_ref.collection(COMMENTS_SUBCOL).document()
    now = datetime.now(timezone.utc)
    comment_data = {"user_id": uid, "text": payload.text, "created_at": now}
    comment_ref.set(comment_data)
    article_ref.update({"comments_count": Increment(1)})
    return CommentOut(id=comment_ref.id, **comment_data)


@router.get("/{article_id}/comments", response_model=List[CommentOut])
def get_comments(article_id: str, limit: int = 50):
    article_ref = db.collection(ARTICLES_COLLECTION).document(article_id)
    if not article_ref.get().exists:
        raise HTTPException(status_code=404, detail="Article not found")
    # FIXED: Use firestore.Query directly
    q = article_ref.collection(COMMENTS_SUBCOL).order_by("created_at", direction=firestore.Query.DESCENDING).limit(limit)
    return [CommentOut(id=c.id, **c.to_dict()) for c in q.stream()]
