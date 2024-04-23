import datetime
import moviepy.editor as mp
from moviepy.editor import *
from PIL import Image
from celery import Celery
from env import CELERY_BROKER_URL, CELERY_TASK_NAME, PROCESSED_FOLDER, UPLOADED_FOLDER
from modelos.modelos import db, Status, Task
from config import app

celery = Celery(CELERY_TASK_NAME, broker=CELERY_BROKER_URL)
app.app_context().push()

# Task - Procesamiento de video: Se encarga de procesar el video subido por el usuario, recortando el video a 20 segundos, ajustando la relación de aspecto a 16:9, añadiendo un logo al inicio y al final del video y guardando el video procesado en la carpeta videos/procesados.
@celery.task()
def process_video(task_id):
    db.engine.dispose()

    task = Task.query.get(task_id)

    if task is None:
        return 'La tarea para el procesamiento del video no fue encontrada'

    video = mp.VideoFileClip(filename=f'./{UPLOADED_FOLDER}/{task.filename}')

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

    video.write_videofile(f'./{PROCESSED_FOLDER}/{task.filename}', codec="libx264")

    task.status = Status.PROCESSED
    task.modified_at = datetime.datetime.now()
    db.session.commit()