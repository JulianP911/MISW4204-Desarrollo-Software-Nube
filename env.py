import os

POSTGRES_USER = os.getenv("POSTGRES_USER", default="postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", default="password")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", default="localhost")
POSTGRES_DB = os.getenv("POSTGRES_DB", default="dbidrl")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", default=4345)

JWT_SECRET_KEY = os.getenv("JWT_SECRET", default="MISW-4204")

UPLOADED_FOLDER = os.getenv("UPLOAD_FOLDER", default="./videos/subidos")
PROCESSED_FOLDER = os.getenv("PROCESSED_FOLDER", default="./videos/procesados")

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", default="redis://localhost:6379/0")
CELERY_TASK_NAME = os.getenv("CELERY_TASK_NAME", default="process_video")

URL_DOWNLOAD = os.getenv("URL_DOWNLOAD", default="http://localhost:5000")
CREDENTIALS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", default="./desarrollo-solucion-nube-095b37877bf3.json")
BUCKET_NAME = os.getenv("BUCKET_NAME", default="desarrollo-solucion-nube")