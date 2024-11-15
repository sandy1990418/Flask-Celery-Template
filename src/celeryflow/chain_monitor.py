import asyncio
from typing import Dict

from celery.result import AsyncResult

from src.celeryflow.data_process import TaskIDExtractor
from src.utils.logger import logger
from src.utils.task_status_db import TaskStatus, save_task_chain, task_status_db

TASK_NAMES = [
    "Check API Healthy",
    "Get QA Datasets",
    "Evaluate Pipeline",
    "Compute Response Score",
]


def extract_chain_ids(items):
    """
    Recursively extract all UUID strings from nested task structures.

    Args:
        Items: The structure containing task results, potentially nested in dictionaries or tuples or AsyncResult.

    Returns:
        list: List of UUID strings found in the structure.
    """
    extractor = TaskIDExtractor()
    return extractor.extract_chain_ids(items)


async def get_task_info(task: AsyncResult, task_name: str, revoke: bool) -> Dict:
    """Asynchronously retrieve information about a single task."""

    # Initialize task info with default values
    task_info = {
        "id": str(task.id),
        "name": task_name,
        "status": task.state,
        "progress": 0,
        "description": "Waiting",
    }

    # TODO: 醜Code 短解
    if task.ready() and task.successful():
        evaluation_result_id = task.result
        if isinstance(evaluation_result_id, Dict):
            task_status = TaskStatus.query.get(task.id)
            if task_status:
                task_status.evaluation_result_id = evaluation_result_id.get(
                    "evaluation_result_id", None
                )
                task_status_db.session.commit()

    try:
        if revoke:
            task.revoke(terminate=True)
            task_info.update({"status": "TERMINATED"})
            return task_info

        # Update task info based on task state
        if task.state == "SUCCESS":
            task_info.update({"progress": 100, "description": "Completed"})
        elif task.state == "FAILURE":
            error_msg = str(task.result) if task.result else "Unknown error"
            task_info.update(
                {"progress": 0, "error": error_msg, "description": "Failed"}
            )
        elif task.state == "PROGRESS" and isinstance(task.info, dict):
            # Extract progress information if available
            progress = task.info.get("progress", 0)
            task_info.update(
                {
                    "progress": progress,
                    "description": task.info.get("description", "Processing"),
                }
            )
        else:
            # Update description when task has started but no progress info is available
            if task.state == "STARTED":
                task_info.update(
                    {
                        "description": "Started",
                    }
                )
    except Exception as e:
        logger.error(f"Error processing task {task.id}: {e}")
        task_info.update({"error": str(e), "description": "Processing Error"})

    return task_info


async def process_exam_result(exam_result: Dict, revoke: bool, root_id: str) -> Dict:
    """Asynchronously process a single exam result, retrieving progress for each subtask."""
    from run import celery_app

    # Extract topic and chain_result from the exam result
    exam_topic = exam_result["Exam Topic"]["topic"]
    chain_result = exam_result["chain_result"]

    # Retrieve all task IDs associated with this exam's chain
    chain_tasks = []
    if isinstance(chain_result, AsyncResult):
        task_ids = extract_chain_ids(chain_result)
        chain_tasks = [celery_app.AsyncResult(tid) for tid in task_ids]

    save_task_chain(root_id, task_ids)

    # Gather status of all tasks in the chain concurrently
    task_names = TASK_NAMES
    tasks_info = await asyncio.gather(
        *[
            get_task_info(task, task_names[i % len(task_names)], revoke)
            for i, task in enumerate(chain_tasks[::-1])
        ]
    )

    # Calculate number of completed tasks for progress tracking
    exam_completed = sum(1 for task in tasks_info if task["status"] == "SUCCESS")
    return {
        "status": tasks_info[0]["status"],
        "topic": exam_topic,
        "tasks": tasks_info,
        "progress": (exam_completed / len(chain_tasks) * 100) if chain_tasks else 0,
        "completed_tasks": exam_completed,
        "total_tasks": len(chain_tasks),
    }


async def get_chain_progress(task_id: str, revoke: bool) -> Dict:
    """Asynchronously retrieve progress information for a task chain by its main task ID."""

    try:
        # Retrieve the main task result
        from run import celery_app

        main_result = celery_app.AsyncResult(task_id)
        results = main_result.info
        # Process each exam result concurrently
        exam_results = await asyncio.gather(
            *[process_exam_result(result, revoke, task_id) for result in results]
        )

        # Calculate total progress across all exams
        total_completed = sum(result["completed_tasks"] for result in exam_results)
        total_tasks = sum(result["total_tasks"] for result in exam_results)
        total_progress = (total_completed / total_tasks * 100) if total_tasks > 0 else 0
        return {
            "state": "SUCCESS" if total_completed == total_tasks else "PROGRESS",
            "progress": {
                "total_progress": total_progress,
                "exam_topics": exam_results,
                "completed_tasks": total_completed,
                "total_tasks": total_tasks,
                "total_exams": len(results),
            },
        }

    except Exception as e:
        logger.error(f"Error in get_chain_progress: {str(e)}")
        return {
            "state": "FAILED",
            "error": str(e),
            "progress": {
                "total_progress": 0,
                "exam_topics": [],
                "completed_tasks": 0,
                "total_tasks": 0,
            },
        }
