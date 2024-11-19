from datetime import datetime
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, Optional

from flask import current_app, request, session
from user_agents import parse

from src.models.controller import BasicController
from src.models.db_schema import OperationHistoryData
from src.utils.data_handler import IdentityHandler
from src.utils.logger import logger


class UserSessionManager:
    def __init__(self):
        self.is_init = False

    def initialize_session(self, user_id: str) -> None:
        if not self.is_init:
            user_agent = parse(request.headers.get("User-Agent", ""))
            session["user_basic_info"] = {
                "user_id": user_id,
                "device_info": user_agent.browser.family,
                "ip_address": str(request.environ.get("HTTP_X_FORWARDED_FOR")),
                "session_start": str(datetime.now()),
            }

            logger.info(f"Get the User Basic Information: {session}")
            self.is_init = True

    def get_user_info(self) -> Dict[str, Any]:
        if "user_basic_info" not in session:
            logger.error("User session not initialized")
            return {}
        return session["user_basic_info"]

    def get_operation(self):
        session["user_basic_info"].update(
            {"operation": request.form.get("button_action", "unknown")}
        )

    def clear_user_session(self) -> None:
        if "user_basic_info" in session:
            session.clear()


class OperationType(Enum):
    CREATE = "Create"
    UPDATE = "Update"
    DELETE = "Delete"
    OTHER = "Other"


class ActionMapper:
    CREATE_KEYWORDS = ["create", "add", "new"]
    UPDATE_KEYWORDS = ["update", "edit", "modify"]
    DELETE_KEYWORDS = ["delete", "remove", "clear"]

    @classmethod
    def get_operation_type(cls, button_action: Optional[str] = None) -> str:
        if not button_action:
            return OperationType.OTHER.value

        action_lower = button_action.lower()

        if any(keyword in action_lower for keyword in cls.CREATE_KEYWORDS):
            return OperationType.CREATE.value
        elif any(keyword in action_lower for keyword in cls.UPDATE_KEYWORDS):
            return OperationType.UPDATE.value
        elif any(keyword in action_lower for keyword in cls.DELETE_KEYWORDS):
            return OperationType.DELETE.value
        else:
            return OperationType.OTHER.value


def user_logger():
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            log_entry = None
            if request.form.get("user_id"):
                current_app.user_session_manager.initialize_session(
                    request.form.get("user_id")
                )
            # current_app.user_session_manager.clear_user_session()
            user_info = current_app.user_session_manager.get_user_info()
            operation_type = request.form.get("button_action", "unknown")
            log_entry = OperationHistoryData(
                user_id=user_info["user_id"],
                operation_type=ActionMapper.get_operation_type(operation_type),
                device_info=user_info["device_info"],
                ip_address=user_info["ip_address"],
                description=f"Function: {func.__name__}, Args: {str(kwargs)}, Operation: {operation_type}",
            )

            controller = BasicController(
                request_handler=IdentityHandler(align_dataclass=OperationHistoryData)
            )
            controller.add_data(request_data=log_entry)

            return func(*args, **kwargs)

        return wrapper

    return decorator
