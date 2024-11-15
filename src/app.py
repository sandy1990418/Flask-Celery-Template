import os

from dotenv import load_dotenv
from flask import Flask
from flask_sse import sse

from src.routes import (
    evaluation_routes,
    main_routes,
    model_routes,
    project_routes,
    user_routes,
)
from src.utils.user_logger import UserSessionManager

load_dotenv(dotenv_path=".env")

src_dir = os.path.dirname(__file__)


def create_app():
    app = Flask(__name__, template_folder="./templates")
    app.register_blueprint(main_routes)
    app.register_blueprint(user_routes)
    app.register_blueprint(project_routes)
    app.register_blueprint(model_routes)
    app.register_blueprint(evaluation_routes)
    app.register_blueprint(sse, url_prefix="/stream")

    app.config["SESSION_TYPE"] = os.getenv("SESSION_TYPE")
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{src_dir}/../db/task_status.db"

    app.user_session_manager = UserSessionManager()

    from src.celeryflow import configure_celery

    celery_app = configure_celery(app)

    return app, celery_app
