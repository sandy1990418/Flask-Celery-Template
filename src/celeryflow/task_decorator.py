import time
from collections import defaultdict
from contextlib import contextmanager
from functools import wraps
from typing import Any, Callable, Dict, Generator

from sqlalchemy import text

from src.utils.logger import logger
from src.utils.task_status_db import task_status_db


class ProgressMonitor:
    """Monitors and tracks the progress of tasks, updating the task's progress status in real-time."""

    def __init__(self, task_instance, total_items, description):
        self.task = task_instance  # The task instance being monitored
        self.total = total_items  # Total number of items to process
        self.current = 0  # Current progress count
        self.description = description  # Description of the task for progress display
        self.start_time = time.time()  # Start to monitor
        self.execution_time = 0  # Execute time

    def update(self):
        """Update progress tracking, incrementing the current count and calculating the percentage progress."""
        self.current += 1
        # Calculate progress percentage, avoiding division by zero
        progress = (self.current / self.total * 100) if self.total > 0 else 0

        self.execution_time = time.time() - self.start_time

        # Update task progress status with details
        self.task.update_progress(
            "PROGRESS",
            {
                "description": f"Processing {self.description} {self.current}/{self.total}",
                "current": self.current,
                "total": self.total,
                "progress": progress,
                "execution_time": self.execution_time,
            },
        )
        logger.info(f"Progress: {progress:.1f}%")  # Log current progress for debugging


class DataView:
    """Provides a memory-efficient view of data without copying it, allowing access to the current item by index."""

    def __init__(self, original_data: Dict, current_index: int):
        self.original_data = original_data  # Original dataset
        self.current_index = current_index  # Index of the current item being processed

    def __getitem__(self, key: int) -> Any:
        """Retrieve the current indexed value for lists or the raw value for non-list entries."""
        value = self.original_data.get(key)
        if isinstance(value, list):
            return (
                [value[self.current_index]] if len(value) > self.current_index else None
            )
        return value

    def get_data(self) -> Dict:
        """Get a view of the data for the current index, including only list entries."""

        return {
            "data": [
                self.original_data[self.current_index]
            ],  # Specific data point for the current index
            **{
                k: self[k]
                for k in self.original_data
                if k != "data"  # and isinstance(self.original_data[k], list)
            },
        }


class PauseController:
    """Controls task execution with pause/resume capability and progress monitoring."""

    def __init__(self, request_id):
        self.request_id = request_id

    @contextmanager
    def pause_check(self):
        """Context manager for checking task pause status."""
        while self.check_pause_status(self.request_id):
            logger.info(f"Task {self.request_id} is paused, waiting...")
            time.sleep(10)
        try:
            yield
        finally:
            pass

    def check_pause_status(self, task_id: str) -> bool:
        result = task_status_db.session.execute(
            text(
                """
                SELECT is_paused
                FROM task_status
                WHERE task_id = :task_id
            """
            ),
            {"task_id": task_id},
        ).scalar()
        task_status_db.session.remove()
        logger.debug(
            f"Here is the task should run or pause, current result is: {result}"
        )
        return bool(result)


def process_items(
    task_func: Callable,
    self: Any,
    data: Dict,
    args: tuple,
    kwargs: dict,
    monitor: ProgressMonitor,
    pause_controller: PauseController,
) -> Generator[Dict, None, None]:
    """Processes each item using a generator to save memory, applying the task function to each item individually."""

    total = len(data)  # Total items to process

    result = defaultdict(list)
    for idx in range(total):
        with pause_controller.pause_check():
            # Create a memory-efficient view of the current data item
            data_view = DataView(data, idx)
            view_data = data_view.get_data()

            # Process each item by calling the task function with view data
            if args:
                result_temp = task_func(self, view_data, *args[1:], **kwargs)
            else:
                result_temp = task_func(self, **{**kwargs, "data": view_data})

        # Update progress monitor
        monitor.update()

        result["result_list"].append(result_temp)
        yield result  # Yield the result for each processed item


def with_progress(description: str):
    """Decorator for memory-efficient progress tracking with detailed status updates."""

    def decorator(task_func):
        @wraps(task_func)
        def wrapped_f(self, *args, **kwargs):
            # Verify if the task instance supports progress tracking
            if not all(hasattr(self, attr) for attr in ["update_progress"]):
                return task_func(self, *args, **kwargs)

            try:
                # Retrieve data from args or kwargs
                data = args[0] if args else kwargs.get("question_data")

                # Initialize progress monitoring based on data length
                total = (
                    len(data)  # ["question_data"]["data"]
                    if isinstance(data, list)  # and "question_data" in data
                    else 1
                )

                monitor = ProgressMonitor(self, total, description)
                pause_controller = PauseController(self.request.id)

                if total != 1:
                    test_paper = args[1]
                    # Process each item with generator for memory efficiency

                    all_results = process_items(
                        task_func, self, data, args, kwargs, monitor, pause_controller
                    )

                    # Initialize result structure to collect processed results
                    result = data.copy()
                    first_result = next(
                        all_results
                    )  # Get the first result to initialize

                    # Set up structure to store list results

                    result.update(
                        {
                            k: []
                            for k in first_result.keys()
                            if isinstance(data.get(k, []), list)
                        }
                    )

                    # Add the first result to the result structure
                    for key in result:
                        if isinstance(first_result.get(key), list):
                            result[key].extend(first_result[key])

                    # Collect and merge remaining results from the generator
                    for processed_result in all_results:
                        for key in result:
                            if isinstance(processed_result.get(key), list):
                                result[key].extend(processed_result[key])

                    test_paper["evaluation_result"].update(
                        {"duration": monitor.execution_time}
                    )
                    return result, test_paper
                else:
                    # If no iterable data, run the task function normally
                    with pause_controller.pause_check():
                        result = task_func(self, *args, **kwargs)
                        monitor.update()

                    # Return final result without additional completion status
                    return result

            except Exception as e:
                # Log any exceptions that occur during processing
                logger.error(f"Task error in {task_func.__name__}: {str(e)}")
                raise

        return wrapped_f

    return decorator
