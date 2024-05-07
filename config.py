import os
from celery import Celery
from flask import Flask
from flask_jwt_extended import JWTManager
from env import (
    CELERY_BROKER_URL,
    POSTGRES_USER,
    POSTGRES_PASSWORD,
    POSTGRES_HOST,
    POSTGRES_PORT,
    POSTGRES_DB,
    JWT_SECRET_KEY,
    UPLOADED_FOLDER,
    PROCESSED_FOLDER,
)
from flask_restful import Api
from modelos.modelos import db

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_pre_ping': True}
app.config["PROPAGATE_EXCEPTIONS"] = True
app.config["JWT_SECRET_KEY"] = JWT_SECRET_KEY

app.config["UPLOADED_FOLDER"] = UPLOADED_FOLDER
app.config["PROCESSED_FOLDER"] = PROCESSED_FOLDER

os.makedirs(app.config["UPLOADED_FOLDER"], exist_ok=True)
os.makedirs(app.config["PROCESSED_FOLDER"], exist_ok=True)

jwt = JWTManager(app)

app_context = app.app_context()
app_context.push()

db.init_app(app)
db.create_all()
