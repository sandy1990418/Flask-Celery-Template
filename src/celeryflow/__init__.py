from celery import Celery
from celery.signals import after_setup_logger, after_setup_task_logger

from src.utils import logger
from src.utils import yaml_data as CONFIG


def setup_logger(celery_logger, **kwargs):
    celery_logger.handlers = []
    for handler in logger.handlers:
        celery_logger.addHandler(handler)

    celery_logger.setLevel(logger.level)
    celery_logger.propagate = False


after_setup_logger.connect(setup_logger)
after_setup_task_logger.connect(setup_logger)


def create_celery(yaml_data: dict):
    broker = yaml_data.pop("broker", None)
    backend = yaml_data.pop("backend", None)

    celery = Celery(__name__, broker=broker, backend=backend)

    # Celery Config
    celery.conf.update(yaml_data)

    celery.conf["imports"] = ("src.celeryflow.tasks",)

    return celery


# Load Config from yaml
celery_app = create_celery(CONFIG["celery_config"])

# Progress track DB
PROGRESS_DATABASE_URL = "sqlite:///db/progress.db"
