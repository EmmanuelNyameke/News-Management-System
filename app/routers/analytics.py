from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, timedelta, timezone
from google.cloud import firestore
from ..firebase import db

router = APIRouter()


# Filter by timeframe
def get_time_range(period: str):
    now = datetime.now(timezone.utc)

    if period == "day":
        return now - timedelta(days=1)
    elif period == "week":
        return now - timedelta(weeks=1)
    elif period == "month":
        return now - timedelta(days=30)
    elif period == "year":
        return now - timedelta(days=365)
    else:
        raise HTTPException(400, "Invalid period. Use day, week, month, or year.")
    

@router.get("/summary")
async def analytics_summary():
    articles = db.collection("articles").stream()

    total_articles = 0
    total_views = 0
    total_likes = 0
    total_comments = 0
    total_shares = 0

    for doc in articles:
        data = doc.to_dict()
        total_articles += 1
        total_views += data.get("views", 0)
        total_likes += data.get("likes_count", 0)
        total_comments += data.get("comments_count", 0)
        total_shares += data.get("shares_count", 0)

    return {
        "total_articles": total_articles,
        "total_views": total_views,
        "total_likes": total_likes,
        "total_comments": total_comments,
        "total_shares": total_shares,
    }

@router.get("/trending")
async def trending_articles(limit: int = 10):
    articles = db.collection("articles").stream()

    ranking = []
    for doc in articles:
        data = doc.to_dict()

        score = (
            data.get("likes_count", 0) * 2 +
            data.get("comments_count", 0) * 3 +
            data.get("shares_count", 0) * 4 +
            data.get("views", 0) * 0.5 
        )

        ranking.append({
            "id": doc.id,
            "title": data.get("title"),
            "thumbnail_url": data.get("thumbnail_url"),
            "score": score,
            "likes": data.get("likes_count", 0),
            "comments": data.get("comments_count", 0),
            "shares": data.get("shares_count", 0),
            "views": data.get("views", 0),
        })

    ranking.sort(key=lambda x: x["score"], reverse=True)

    return ranking[:limit]


@router.get("/activity")
async def activity_chart(period: str = Query(..., description="day, week, month, year")):
    start_time = get_time_range(period)
    articles = db.collection("articles").stream()

    labels = []
    values = []

    for doc in articles:
        data = doc.to_dict()
        created_at = data.get("created_at")

        if created_at and created_at >= start_time:
            labels.append(data.get("title"))
            values.append({
                "likes": data.get("likes_count", 0),
                "comments": data.get("comments_count", 0),
                "shares": data.get("shares_count", 0),
                "views": data.get("views", 0),
            })

    return {
        "period": period,
        "labels": labels,
        "datasets": values,
    }


@router.get("/{slug}/detail")
async def article_detail_analytics(slug: str):
    doc = db.collection("articles").document(slug).get()
    if not doc.exists:
        raise HTTPException(404, "Article not found")
    
    data = doc.to_dict()

    return {
        "id": slug,
        "title": data.get("title"),
        "views": data.get("views", 0),
        "likes": data.get("likes_count", 0),
        "comments": data.get("comments_count", 0),
        "shares": data.get("shares_count", 0),
        "created_at": data.get("created_at"),
        "updated_at": data.get("updated_at"),
    }
