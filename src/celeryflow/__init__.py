from celery import Celery
from celery.signals import after_setup_logger, after_setup_task_logger

from src.utils.load_yaml import yaml_data as CONFIG
from src.utils.logger import logger


def setup_logger(celery_logger, **kwargs):
    celery_logger.handlers = []
    for handler in logger.handlers:
        celery_logger.addHandler(handler)

    celery_logger.setLevel(logger.level)
    celery_logger.propagate = False


after_setup_logger.connect(setup_logger)
after_setup_task_logger.connect(setup_logger)


def create_celery(yaml_data: dict):
    broker = yaml_data.get("broker", None)
    backend = yaml_data.get("backend", None)

    celery = Celery(__name__, broker=broker, backend=backend)

    # Celery Config
    celery.conf.update(yaml_data)

    celery.conf.update(
        imports=("src.celeryflow.tasks",),
        result_extended=True,
    )
    return celery


# Load Config from yaml
def configure_celery(app=None):
    celery = create_celery(CONFIG["celery_config"])

    if app:

        class ContextTask(celery.Task):
            def __call__(self, *args, **kwargs):
                with app.app_context():
                    return self.run(*args, **kwargs)

        celery.Task = ContextTask
        celery.conf.update(app.config)
    return celery


# Initialize celery without Flask context
celery_app = configure_celery()
