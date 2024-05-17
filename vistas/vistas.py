import base64
import os
import tempfile
import datetime
import moviepy.editor as mp
from moviepy.editor import *
from PIL import Image
from env import BUCKET_NAME, PROCESSED_FOLDER, UPLOADED_FOLDER, URL_DOWNLOAD, TOPIC_NAME
from flask_restful import Resource
from flask import request, send_file
from modelos import User, db
from datetime import timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required

from modelos.modelos import Extension, Status, Task, TaskSchema
from google.cloud import storage
from google.cloud import pubsub_v1

task_schema = TaskSchema()

storage_client = storage.Client()

publisher = pubsub_v1.PublisherClient()

class VistaSignUp(Resource):

    # POST - Permite crear una cuenta con los campos para nombre de usuario, correo electrónico y contraseña.
    def post(self):
        username = request.json["username"]
        password1 = request.json["password1"]
        password2 = request.json["password2"]
        email = request.json["email"]

        if not username or not password1 or not password2 or not email:
            return {
                "message": "Todos los campos deben ser enviados (username, password1, password2 y email)"
            }, 400

        user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()

        if user is None:
            if password1 == password2:
                encrypted_password = generate_password_hash(password1)
                user = User(username=username, password=encrypted_password, email=email)
                db.session.add(user)
                db.session.commit()
                return {"message": "Usuario creado exitosamente"}, 201
            else:
                return {"message": "Las contrasenias no coinciden"}, 400
        else:
            return {
                "message": "El usuario con ese tipo de nombre de usuario y email ya existe, intenta con otro"
            }, 409


class VistaLogin(Resource):

    # POST - Permite iniciar sesión con los campos de nombre de usuario y contraseña.
    def post(self):
        username = request.json["username"]
        password = request.json["password"]

        if not username or not password:
            return {
                "message": "Todos los campos deben ser enviados (username y password)"
            }, 400

        user = User.query.filter(User.username == username).first()

        if user is not None:
            verification_password = check_password_hash(user.password, password)
            if not verification_password:
                return {"message": "Contrasenia invalidad, intenta nuevamente"}, 400
            else:
                try:
                    token = create_access_token(
                        identity=username, expires_delta=timedelta(days=1)
                    )
                    return {"message": "Inicio de sesion exitoso", "token": token}, 200
                except:
                    return {"message": "Inicio de sesion fallido"}, 500
        else:
            return {"message": "Usuario no encontrado en el sistema"}, 404


class VistaTask(Resource):

    # POST - Permite crear una nueva tarea de edición de video. El usuario requiere autorización.
    @jwt_required()
    def post(self):
        file = request.files["filename"]

        if not file:
            return {"message": "El campo filename es requerido"}, 400

        filename = file.filename
        file_split = file.filename.split(".")
        file_extension = file_split[1]

        if file_extension not in ["mp4", "mov", "wmv", "avi"]:
            return {
                "message": "El archivo no tiene una extension valida para su procesamiento"
            }, 400

        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(UPLOADED_FOLDER + '/' + filename)
        blob.upload_from_string(file.read(), content_type=file.content_type)

        username = get_jwt_identity()
        user = User.query.filter(User.username == username).first()

        task = Task(
            filename=filename,
            extension=file_extension.upper(),
            status=Status.UPLOADED,
            user_id=user.id,
        )
        db.session.add(task)
        db.session.commit()

        publisher.publish(TOPIC_NAME, str(task.id).encode())

        return task_schema.dump(task), 200

    # DELETE - Permite eliminar una tarea en la aplicación. El usuario requiere autorización.
    @jwt_required()
    def delete(self, task_id):
        username = get_jwt_identity()
        task = Task.query.get(task_id)
        user = User.query.filter(User.username == username).first()

        if task is None:
            return {"message": "El archivo no existe"}, 404

        if task.status != Status.PROCESSED:
            return {"message": "El archivo no ha sido procesado"}, 400

        if task.user_id != user.id:
            return {"message": "El usuario no es propietario del archivo"}, 400
        try:
            # Eliminar archivos del sistema
            bucket = storage_client.bucket(BUCKET_NAME)
            blob = bucket.blob(UPLOADED_FOLDER + '/' + task.filename)
            blob.delete()
            blob = bucket.blob(PROCESSED_FOLDER + '/' + task.filename)
            blob.delete()

            # Eliminarlo de la DB
            db.session.delete(task)
            db.session.commit()

            return "", 204

        except Exception as e:
            # If any error occurs during file deletion or database operation
            db.session.rollback()
            return {"message": "Error al eliminar el archivo: {}".format(str(e))}, 500

    # GET - Lista las tareas de un usuario.
    @jwt_required()
    def get(self):
        username = get_jwt_identity()
        user = User.query.filter(User.username == username).first()

        if user is None:
            return {"message": "Usuario no encontrado en el sistema"}, 404

        tasks = Task.query.filter(Task.user_id == user.id).all()

        if not tasks:
            return {"message": "No hay tareas de edición para este usuario"}, 404

        task_list = []
        for task in tasks:
            task_info = {
                "id": task.id,
                "filename": task.filename,
                "status": task.status,
            }
            task_list.append(task_schema.dump(task_info))

        return {"tasks": task_list}, 200


class VistaTaskDetail(Resource):
    # GET - Permite obtener información de una tarea específica.
    @jwt_required()
    def get(self, task_id):
        username = get_jwt_identity()
        user = User.query.filter(User.username == username).first()

        if user is None:
            return {"message": "Usuario no encontrado en el sistema"}, 404

        task = Task.query.get(task_id)

        if task is None:
            return {"message": "El archivo no existe"}, 404
        if task.user_id != user.id:
            return {"message": "El usuario no es propietario del archivo"}, 400

        task_info = task_schema.dump(task)
        if task.status == Status.PROCESSED:
            task_info["path"] = PROCESSED_FOLDER + "/" + task.filename
            task_info["url"] = "{}/api/tasks/{}/download".format(URL_DOWNLOAD, task.id)

        return task_info, 200


class VistaDownloadTask(Resource):

    # GET - Permite descargar un archivo procesado.
    @jwt_required()
    def get(self, task_id):
        username = get_jwt_identity()
        user = User.query.filter(User.username == username).first()

        if user is None:
            return {"message": "Usuario no encontrado en el sistema"}, 404

        task = Task.query.get(task_id)

        if task is None:
            return {"message": "El archivo no existe"}, 404
        if task.user_id != user.id:
            return {"message": "El usuario no es propietario del archivo"}, 400

        if task.status == Status.PROCESSED:
            bucket = storage_client.bucket(BUCKET_NAME)
            blob = bucket.blob(PROCESSED_FOLDER + "/" + task.filename)
            blob.download_to_filename('/tmp/' + task.filename)
            return send_file('/tmp/' + task.filename, as_attachment=True)

        return {
            "message": "El archivo no ha sido procesado por lo cual no se puede descargar"
        }, 400

def list_files(directory):
    """
    List all files in the given directory and its subdirectories.
    """
    for root, _, files in os.walk(directory):
        for file in files:
            yield os.path.join(root, file)

class VistaProcessTask(Resource):

    # POST - Permite procesar un video.
    def post(self):
        task_id = request.json["message"]["data"]
        task = Task.query.get(int(base64.b64decode(task_id).decode('utf-8')))

        if task is None:
            message = 'La tarea para el procesamiento del video no fue encontrada'
            return message

        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(f'{UPLOADED_FOLDER}/{task.filename}')
        blob.download_to_filename(task.filename)

        video = mp.VideoFileClip(filename=f'./{task.filename}')

        end_time = 20
        video = video.subclip(0, end_time - 1)

        new_width = int(video.h * 16 / 9)
        video = vfx.crop(video, x1=0, y1=0, width=new_width, height=video.h)

        end_time = 20
        video = video.subclip(1, end_time - 1)

        image = Image.open('./logos/IDRL.jpeg')
        image_resized = image.resize((video.w, video.h))
        image_resized.save('./logos/IDRL.jpeg')

        image_clip = mp.ImageClip('./logos/IDRL.jpeg', duration=1)
        video = mp.concatenate_videoclips([image_clip, video, image_clip])

        video.write_videofile(f'./{task.filename}', codec="libx264")
        blob = bucket.blob(f'{PROCESSED_FOLDER}/{task.filename}')
        blob.upload_from_filename(f'./{task.filename}')

        task.status = Status.PROCESSED
        task.modified_at = datetime.datetime.now()
        db.session.commit()

        return 200