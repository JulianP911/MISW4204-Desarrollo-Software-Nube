from celery import Celery
from config import app
from flask_restful import Api

from vistas.vistas import (
    VistaDownloadTask,
    VistaLogin,
    VistaProcessTask,
    VistaSignUp,
    VistaTask,
    VistaTaskDetail,
)

api = Api(app)
api.add_resource(VistaSignUp, "/api/auth/signup")
api.add_resource(VistaLogin, "/api/auth/login")
api.add_resource(VistaTaskDetail, "/api/tasks/<int:task_id>")
api.add_resource(VistaTask, "/api/tasks", "/api/tasks/<int:task_id>")
api.add_resource(VistaDownloadTask, "/api/tasks/<int:task_id>/download")
api.add_resource(VistaProcessTask, "/api/tasks/process")

if __name__ == "__main__":
    app.run()
