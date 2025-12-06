import os
import json
from dotenv import load_dotenv

# Load .env file automatically
load_dotenv()

FIREBASE_SA_JSON = os.environ.get("FIREBASE_SERVICE_ACCOUNT")
FIREBASE_STORAGE_BUCKET = os.environ.get("FIREBASE_STORAGE_BUCKET")

if not FIREBASE_SA_JSON:
    raise RuntimeError("Set FIREBASE_SERVICE_ACCOUNT in .env")
if not FIREBASE_STORAGE_BUCKET:
    raise RuntimeError("Set FIREBASE_STORAGE_BUCKET in .env")

FIREBASE_SERVICE_ACCOUNT = json.loads(FIREBASE_SA_JSON)