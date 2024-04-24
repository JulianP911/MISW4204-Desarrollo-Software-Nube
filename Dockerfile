FROM ubuntu:latest

RUN apt update
RUN apt install python3 python3-pip -y
RUN apt install ffmpeg -y
RUN apt install libpq-dev -y

WORKDIR /cloud-docker

ENV POSTGRES_HOST="postgres"
ENV POSTGRES_PORT="5432"
ENV POSTGRES_DB="dbidrl"
ENV POSTGRES_PASSWORD="password"
ENV POSTGRES_USER="postgres"
ENV JWT_SECRET="MISW-4204"
ENV UPLOAD_FOLDER="videos-subidos"
ENV PROCESSED_FOLDER="videos-procesados"
ENV CELERY_BROKER_URL="redis://redis:6379/0"
ENV CELERY_TASK_NAME='process_video'


COPY . .
RUN pip3 install -r requirements.txt

EXPOSE 8080



