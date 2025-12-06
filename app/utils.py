import tempfile, os, uuid
from fastapi import UploadFile
from .firebase import gcs_bucket

def upload_file_to_storage(upload: UploadFile, dest_folder: str = "articles") -> str:
    ext = os.path.splitext(upload.filename)[1]
    blob_name = f"{dest_folder}/{uuid.uuid4().hex}{ext}"
    blob = gcs_bucket.blob(blob_name)

    # Save to temp file
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(upload.file.read())
        tmp.flush()

    try:
        blob.upload_from_filename(tmp.name, content_type=upload.content_type)
        blob.make_public() # Public for mobile client
        return blob.public_url
    finally:
        try:
            os.unlink(tmp.name)
        except Exception:
            pass

