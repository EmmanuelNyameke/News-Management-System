import firebase_admin
from firebase_admin import credentials, firestore, storage
from google.cloud import storage as gcs
from google.oauth2 import service_account
from .config import FIREBASE_SERVICE_ACCOUNT, FIREBASE_STORAGE_BUCKET

# Initialize Firebase Admin
if not firebase_admin._apps:
    # CORRECT: Use credentials.Certificate() with a dictionary
    cred = credentials.Certificate(FIREBASE_SERVICE_ACCOUNT)
    firebase_admin.initialize_app(cred, {
        "storageBucket": FIREBASE_STORAGE_BUCKET
    })

# Firestore client
db = firestore.client()

# Storage clients
bucket = storage.bucket()  # Firebase admin bucket

# Create GCS client using the service account info
gcs_credentials = service_account.Credentials.from_service_account_info(FIREBASE_SERVICE_ACCOUNT)
gcs_client = gcs.Client(
    credentials=gcs_credentials, 
    project=FIREBASE_SERVICE_ACCOUNT['project_id']
)
gcs_bucket = gcs_client.bucket(FIREBASE_STORAGE_BUCKET)