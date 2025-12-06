from fastapi import Header, HTTPException
from firebase_admin import auth


def verify_firebase_token(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid auth header")
    id_token = authorization.split("Bearer ")[1]
    try:
        decoded = auth.verify_id_token(id_token)
        return decoded
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid Firebase token")