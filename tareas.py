import datetime
import tempfile
import os
import moviepy.editor as mp
from moviepy.editor import *
from PIL import Image
from celery import Celery
from env import BUCKET_NAME, PROCESSED_FOLDER, UPLOADED_FOLDER, SUBSCRIPTION_NAME
from modelos.modelos import db, Status, Task
from config import app
from google.cloud import storage
from google.cloud import pubsub_v1

storage_client = storage.Client()

# Task - Procesamiento de video: Se encarga de procesar el video subido por el usuario, recortando el video a 20 segundos, ajustando la relación de aspecto a 16:9, añadiendo un logo al inicio y al final del video y guardando el video procesado en la carpeta videos/procesados.
def process_video(message):
    app.app_context().push()
    db.engine.dispose()

    task = Task.query.get(int(message.data))

    if task is None:
        message = 'La tarea para el procesamiento del video no fue encontrada'
        print(message)
        return message

    with tempfile.NamedTemporaryFile(delete=False) as temp_input_file:
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(f'{UPLOADED_FOLDER}/{task.filename}')
        blob.download_to_filename(temp_input_file.name)

        video = mp.VideoFileClip(filename=temp_input_file.name)

        end_time = 20
        video = video.subclip(0, end_time - 1)

        new_width = int(video.h * 16 / 9)
        video = vfx.crop(video, x1=0, y1=0, width=new_width, height=video.h)

        end_time = 20
        video = video.subclip(1, end_time - 1)

        with tempfile.NamedTemporaryFile(delete=False) as temp_middle_file:

            blob = bucket.blob(f'logos/IDRL.jpeg')
            blob.download_to_filename(temp_middle_file.name)

            image = Image.open(temp_middle_file.name)
            image_resized = image.resize((video.w, video.h))
            image_resized.save(temp_middle_file.name, 'jpeg')

            image_clip = mp.ImageClip(temp_middle_file.name, duration=1)
            video = mp.concatenate_videoclips([image_clip, video, image_clip])

            temp_middle_file.close()

            with tempfile.NamedTemporaryFile(delete=False) as temp_output_file:
                if not os.path.exists('./video-procesado'):
                    os.makedirs('./video-procesado')
                video.write_videofile(f'./video-procesado/{task.filename}', codec='libx264')
                blob = bucket.blob(f'{PROCESSED_FOLDER}/{task.filename}')
                blob.upload_from_filename(f'./video-procesado/{task.filename}')

                task.status = Status.PROCESSED
                task.modified_at = datetime.datetime.now()
                db.session.commit()

            temp_output_file.close()

    temp_input_file.close()


subscriber = pubsub_v1.SubscriberClient()
subscription_path = SUBSCRIPTION_NAME

streaming_pull_future = subscriber.subscribe(subscription_path, callback=process_video)
print(f'Listening for tasks on {subscription_path}..\n')

streaming_pull_future.result()