import asyncio

from hypercorn.asyncio import serve
from hypercorn.config import Config

from src.app import create_app
from src.utils.task_status_db import task_status_db

app, celery_app = create_app()

task_status_db.init_app(app)

with app.app_context():
    task_status_db.create_all()

app.app_context().push()

if __name__ == "__main__":
    config = Config()
    config.bind = ["0.0.0.0:5000"]
    asyncio.run(serve(app, config))
