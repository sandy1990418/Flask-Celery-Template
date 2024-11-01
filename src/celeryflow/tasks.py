import requests

from src.celeryflow import celery_app
from src.celeryflow.task_decorator import with_progress
from src.celeryflow.task_tracker import CeleryBaseTask
from src.utils.logger import logger


@celery_app.task(bind=True, name="template.check_api_health", base=CeleryBaseTask)
@with_progress("Checking health for API")
def check_health(
    api_health_endpoints: str = "https://status.openai.com/api/v2/status.json",
):
    """Check API health status and pass data if healthy"""

    logger.info(f"Checking health for API: {api_health_endpoints}")
    try:
        response = requests.get(api_health_endpoints)
        is_healthy = response.status_code == requests.codes.ok
        if is_healthy:
            logger.info("API health check!")
            return
    except Exception as e:
        logger.error(f"API health check error: {str(e)}")
    logger.error("API health check failed !")
