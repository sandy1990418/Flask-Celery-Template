from typing import Dict, Optional

from celery import Task

from src.celeryflow.data_process import DataFrameSerializer
from src.utils.logger import logger


class TaskProgressTracker:
    """Mixin for tracking task progress and state updates.

    Provides comprehensive task progress monitoring capabilities including:
    - State updates with metadata
    - Progress percentage calculation
    - Detailed logging of task execution stages
    - Chain ID tracking for task pipeline monitoring
    """

    def __init__(self):
        self._state = None

    def update_progress(self, state: str, meta: Dict = None) -> None:
        """Update task state and log progress details.

        Args:
            state: Current state of the task (e.g., 'PROGRESS', 'SUCCESS')
            meta: Optional metadata dictionary containing progress information
        """
        try:
            meta = meta or {}
            if hasattr(self, "chain_id"):
                meta["chain_id"] = self.chain_id

            # Check if we're running as a Celery task
            if hasattr(self, "update_state"):
                self.update_state(state=state, meta=meta)
            else:
                logger.warning("Not running as Celery task - progress updates disabled")

            progress = meta.get("progress", 0)
            description = meta.get("description", "")
            current = meta.get("current", 0)
            total = meta.get("total", 0)
            logger.info("Task Progress Update:")
            logger.info(f"└── Chain ID: {getattr(self, 'chain_id', 'N/A')}")
            logger.info(f"    ├── Task Description: {description}")
            logger.info(f"    ├── Task ID: {self.request.id}")
            logger.info(f"    ├── State: {state}")
            logger.info(f"    ├── Progress: {progress:.1f}%")
            logger.info(f"    └── Current/Total: {current}/{total}")

            logger.info(f"Task Progress: {progress}% - {description}")

        except Exception as e:
            logger.error(f"Error updating progress: {e}")

    def set_progress(self, current: int, total: int, description: str = None) -> None:
        """Set task progress with calculated percentage and metadata.

        Args:
            current: Current progress value
            total: Total expected value for completion
            description: Optional progress description
        """
        try:
            progress = (current / total * 100) if total > 0 else 0
            self.update_progress(
                "PROGRESS",
                {
                    "current": current,
                    "total": total,
                    "progress": progress,
                    "description": description or f"Processing {current}/{total}",
                },
            )
        except Exception as e:
            logger.error(f"Error setting progress: {e}")

    def start_task(self, total: int, description: str = None) -> None:
        """Initialize task with total expected items and starting state.

        Args:
            total: Total number of items to process
            description: Optional task description
        """
        self.set_progress(0, total, description or "Starting task...")

    def complete_task(self, description: str = None) -> None:
        """Mark task as successfully completed with 100% progress."""
        self.update_progress(
            "SUCCESS", {"progress": 100, "description": description or "Task completed"}
        )

    def fail_task(self, error: str) -> None:
        """Mark task as failed with error details.

        Args:
            error: Error message describing the failure
        """
        self.update_progress(
            "FAILURE",
            {
                "progress": 0,
                "error": str(error),
                "description": f"Task failed: {error}",
            },
        )

    def update_item_progress(
        self, current: int, total: int, description: str = None
    ) -> None:
        """Update progress for individual item processing.
                "error": str(error),
        Args:
            current: Current item number
            total: Total number of items
            description: Optional description of current progress
        """
        try:
            progress = (current / total * 100) if total > 0 else 0
            self.update_progress(
                "PROGRESS",
                {
                    "current": current,
                    "total": total,
                    "progress": progress,
                    "description": description or f"Processing item {current}/{total}",
                },
            )
        except Exception as e:
            logger.error(f"Error updating item progress: {e}")


class TaskChainTracker:
    """Mixin for managing task chain relationships and tracking.

    Provides functionality to track task execution within a larger chain/pipeline
    of tasks, maintaining chain context across task boundaries.
    """

    def __init__(self):
        self._chain_id = None

    @property
    def chain_id(self) -> Optional[str]:
        """Get the chain identifier for the current task execution.

        Returns:
            str: Chain ID from request headers if available
        """
        if not hasattr(self, "_chain_id"):
            self._chain_id = None
        if self._chain_id is None:
            headers = getattr(self.request, "headers", {}) or {}
            self._chain_id = headers.get("chain_id")
        return self._chain_id


class CeleryBaseTask(Task, TaskProgressTracker, TaskChainTracker, DataFrameSerializer):
    """Base Celery task class combining progress tracking, data serialization,
    and chain management capabilities."""

    abstract = True

    def __init__(self):
        Task.__init__(self)
        TaskProgressTracker.__init__(self)
        TaskChainTracker.__init__(self)
        DataFrameSerializer.__init__(self)
        self._chain_id = None
        self._state = None

    def __call__(self, *args, **kwargs):
        # Ensure all mixins are properly initialized before task execution
        if not hasattr(self, "_initialized"):
            self.__init__()
            self._initialized = True
        return super().__call__(*args, **kwargs)

    # Add required progress tracking methods
    def start_task(self, total: int, description: str = None):
        TaskProgressTracker.start_task(self, total, description)

    def complete_task(self, description: str = None):
        TaskProgressTracker.complete_task(self, description)

    def fail_task(self, error: str):
        TaskProgressTracker.fail_task(self, error)

    def set_progress(self, current: int, total: int, description: str = None):
        TaskProgressTracker.set_progress(self, current, total, description)

    def update_progress(self, state: str, meta: Dict = None):
        TaskProgressTracker.update_progress(self, state, meta)

    def update_item_progress(
        self, current: int, total: int, description: str = None
    ) -> None:
        TaskProgressTracker.update_item_progress(self, current, total, description)
