import json
from typing import List

from flask_sqlalchemy import SQLAlchemy

from src.utils.logger import logger

task_status_db = SQLAlchemy()


class TaskStatus(task_status_db.Model):
    __tablename__ = "task_status"
    task_id = task_status_db.Column(task_status_db.String(50), primary_key=True)
    status = task_status_db.Column(task_status_db.String(50), default=False)
    is_paused = task_status_db.Column(task_status_db.Boolean, default=False)
    child_task_id = task_status_db.Column(task_status_db.String(50), nullable=True)
    child_task_ids = task_status_db.Column(task_status_db.Text, nullable=True)
    root_task_id = task_status_db.Column(task_status_db.String(50), nullable=True)
    evaluation_result_id = task_status_db.Column(
        task_status_db.String(50), nullable=True
    )  # 新增此行

    @property
    def child_tasks(self) -> List[str]:
        if self.child_task_ids:
            return json.loads(self.child_task_ids)
        return []

    @child_tasks.setter
    def child_tasks(self, task_ids: List[str]):
        self.child_task_ids = json.dumps(task_ids) if task_ids else None


def save_task_chain(root_id: str, task_ids: List[str]):
    root_status = TaskStatus.query.get(root_id) or TaskStatus(task_id=root_id)
    root_status.child_tasks = task_ids
    root_status.root_task_id = root_id
    task_status_db.session.merge(root_status)

    for task_id in task_ids:
        child_status = TaskStatus.query.get(task_id) or TaskStatus(task_id=task_id)
        child_status.root_task_id = root_id
        task_status_db.session.merge(child_status)

    task_status_db.session.commit()


def update_task_state(task_id: str, status: str, is_paused: bool) -> bool:
    """Update task state and all related tasks"""
    try:
        task = TaskStatus.query.get(task_id)
        if not task:
            logger.error(f"Task not found: {task_id}")
            return False

        root_task_id = task.root_task_id or task_id

        logger.info(f"Current task status: {task.status}, is_paused: {task.is_paused}")

        # 執行更新
        updated_rows = TaskStatus.query.filter(
            (TaskStatus.task_id == root_task_id)
            | (TaskStatus.root_task_id == root_task_id)
        ).update({"status": status, "is_paused": is_paused}, synchronize_session=False)

        task_status_db.session.commit()

        logger.info(f"Updated {updated_rows} task records")

        return True

    except Exception as e:
        logger.error(f"Update task state error: {str(e)}")
        task_status_db.session.rollback()
        return False


def get_evaluation_result_id(task_id: str):
    results = (
        TaskStatus.query.filter(
            (TaskStatus.root_task_id == task_id)
            & (TaskStatus.evaluation_result_id.isnot(None))
        )
        .with_entities(TaskStatus.evaluation_result_id)
        .all()
    )
    return {"evaluation_result_ids": [int(result[0]) for result in results]}
