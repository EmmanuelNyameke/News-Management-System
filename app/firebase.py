import firebase_admin
from firebase_admin import credentials, firestore, storage
from google.cloud import storage as gcs
from .config import FIREBASE_SA_JSON, FIREBASE_STORAGE_BUCKET

# Initlialize Firebase Admin
if not firebase_admin._apps:
    cred = credentials.Certificate(FIREBASE_SA_JSON)
    firebase_admin.initialize_app(cred, {"storageBucket": FIREBASE_STORAGE_BUCKET})

# Firestore client
db = firestore.client()

# Storage clients
bucket = storage.bucket() # Firebase admin bucket
gcs_client = gcs.Client.from_service_account_json(FIREBASE_SA_JSON)
gcs_bucket = gcs.client.Bucket(FIREBASE_STORAGE_BUCKET)