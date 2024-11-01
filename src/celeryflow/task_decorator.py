from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, Generator, TypeVar

from src.utils.logger import logger

T = TypeVar("T")


class TaskState(Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ProgressMonitor:
    def __init__(self, task_instance, total_items, description):
        self.task = task_instance
        self.total = total_items
        self.current = 0
        self.description = description

    def update(self):
        """Update progress tracking"""
        self.current += 1
        progress = (self.current / self.total * 100) if self.total > 0 else 0

        self.task.update_progress(
            "PROGRESS",
            {
                "current": self.current,
                "total": self.total,
                "progress": progress,
                "description": f"Processing {self.description} {self.current}/{self.total}",
            },
        )
        logger.info(f"Progress: {progress:.1f}%")


class DataView:
    """Memory efficient data view that doesn't copy the underlying data"""

    def __init__(self, original_data: Dict, current_index: int):
        self.original_data = original_data
        self.current_index = current_index

    def __getitem__(self, key: str) -> Any:
        value = self.original_data.get(key)
        if isinstance(value, list):
            return (
                [value[self.current_index]] if len(value) > self.current_index else None
            )
        return value

    def get_data(self) -> Dict:
        """Get a view of the data for the current index"""
        return {
            "data": [self.original_data["data"][self.current_index]],
            **{
                k: self[k]
                for k in self.original_data
                if k != "data" and isinstance(self.original_data[k], list)
            },
        }


def process_items(
    task_func: Callable,
    self: Any,
    data: Dict,
    args: tuple,
    kwargs: dict,
    monitor: ProgressMonitor,
) -> Generator[Dict, None, None]:
    """Process items one by one using generator to save memory"""
    total = len(data["data"])
    for idx in range(total):
        # Create a view instead of copying data
        data_view = DataView(data, idx)
        view_data = data_view.get_data()

        # Process single item
        if args:
            result = task_func(self, view_data, *args[1:], **kwargs)
        else:
            result = task_func(self, **{**kwargs, "data": view_data})

        # Update progress
        monitor.update()
        yield result


def with_progress(description: str):
    """Memory efficient progress tracking decorator"""

    def decorator(task_func):
        @wraps(task_func)
        def wrapped_f(self, *args, **kwargs):
            # Verify progress tracking capabilities
            if not all(hasattr(self, attr) for attr in ["update_progress"]):
                return task_func(self, *args, **kwargs)

            try:
                # Get data
                data = args[0] if args else kwargs.get("data")
                if not data:
                    return task_func(self, *args, **kwargs)

                # Setup progress monitoring
                total = (
                    len(data["data"])
                    if isinstance(data, dict) and "data" in data
                    else 1
                )
                monitor = ProgressMonitor(self, total, description)

                if isinstance(data, dict) and "data" in data:
                    # Process items using generator
                    all_results = process_items(
                        task_func, self, data, args, kwargs, monitor
                    )

                    # Efficiently collect results
                    result = data.copy()
                    first_result = next(all_results)
                    result.update(
                        {
                            k: []
                            for k in first_result.keys()
                            if isinstance(data.get(k, []), list)
                        }
                    )

                    # Add the first result
                    for key in result:
                        if isinstance(first_result.get(key), list):
                            result[key].extend(first_result[key])

                    # Merge remaining results efficiently
                    for processed_result in all_results:
                        for key in result:
                            if isinstance(processed_result.get(key), list):
                                result[key].extend(processed_result[key])
                else:
                    result = task_func(self, *args, **kwargs)
                    monitor.update()

                # Do not send additional completion status
                return result

            except Exception as e:
                logger.error(f"Task error in {task_func.__name__}: {str(e)}")
                raise

        return wrapped_f

    return decorator
