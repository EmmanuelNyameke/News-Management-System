from fastapi import APIRouter, HTTPException
from typing import List
from datetime import datetime, timezone
from google.cloud import firestore

from .articles import ARTICLES_COLLECTION
from ..firebase import db
from ..models import CommentIn, CommentOut
from google.cloud.firestore_v1 import Increment
from google.cloud.firestore_v1.base_document import DocumentSnapshot

router = APIRouter()
COMMENTS_SUBCOL = "comments"


def convert_firestore_timestamp(timestamp):
    """Convert Firestore timestamp to regular datetime"""
    if hasattr(timestamp, 'isoformat'):
        # If it's already a datetime-like object
        return timestamp
    elif hasattr(timestamp, 'timestamp'):
        # Convert to datetime
        return timestamp
    return timestamp


def prepare_comment_data(doc: DocumentSnapshot):
    """Prepare comment data for response, converting timestamps"""
    data = doc.to_dict()
    data["id"] = doc.id
    
    # Convert Firestore timestamp to regular datetime
    if "created_at" in data:
        data["created_at"] = convert_firestore_timestamp(data["created_at"])
    
    return data


@router.post("/{article_id}/comments", response_model=CommentOut)
def post_comment(article_id: str, payload: CommentIn):
    # Removed auth requirement
    user_id = "ViKay"  # Default user ID
    article_ref = db.collection(ARTICLES_COLLECTION).document(article_id)
    if not article_ref.get().exists:
        raise HTTPException(status_code=404, detail="Article not found")
    
    comment_ref = article_ref.collection(COMMENTS_SUBCOL).document()
    now = datetime.now(timezone.utc)
    comment_data = {
        "user_id": user_id, 
        "text": payload.text, 
        "created_at": now
    }
    comment_ref.set(comment_data)
    article_ref.update({"comments_count": Increment(1)})
    
    return CommentOut(id=comment_ref.id, **comment_data)


@router.get("/{article_id}/comments", response_model=List[CommentOut])
def get_comments(article_id: str, limit: int = 50):
    article_ref = db.collection(ARTICLES_COLLECTION).document(article_id)
    if not article_ref.get().exists:
        raise HTTPException(status_code=404, detail="Article not found")
    
    q = article_ref.collection(COMMENTS_SUBCOL).order_by("created_at", direction=firestore.Query.DESCENDING).limit(limit)
    comments = []
    for doc in q.stream():
        data = prepare_comment_data(doc)
        comments.append(CommentOut(**data))
    
    return comments