from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import articles, comments, likes_shares, sitemap, analytics

app = FastAPI(title="Blog CMS")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)


app.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
app.include_router(articles.router, prefix="/articles", tags=["articles"])
app.include_router(comments.router, prefix="/articles", tags=["comments"])
app.include_router(likes_shares.router, prefix="/articles", tags=["likes_shares"])
app.include_router(sitemap.router, tags=["sitemap"])