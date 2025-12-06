from fastapi import APIRouter, Response

from .articles import ARTICLES_COLLECTION
from ..firebase import db

router = APIRouter()

@router.get("/sitemap.xml", response_class=Response)
async def sitemap():
    articles = db.collection(ARTICLES_COLLECTION).stream()
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for doc in articles:
        slug = doc.id
        xml += f"<url><loc>https://vikayblog.com/articles/{slug}</loc></url>\n"
    xml += "</urlset>"
    return Response(content=xml, media_type="application/xml")
