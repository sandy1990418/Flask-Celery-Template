from abc import ABC, abstractmethod
from dataclasses import dataclass, fields
from datetime import datetime


@dataclass
class BaseSchema(ABC):
    created_at: datetime = None
    status: int = None

    @classmethod
    def from_dict(cls, data: dict):
        cls_key = {field.name for field in fields(cls)}
        cls_fields = {key: data.get(key, None) for key in cls_key}
        return cls(**cls_fields)

    @staticmethod
    @abstractmethod
    def get_table_name():
        pass

    @staticmethod
    @abstractmethod
    def get_primary_key_name():
        pass


@dataclass
class ProjectData(BaseSchema):
    project_id: int = None
    project_name: str = None
    description: str = None

    @staticmethod
    def get_table_name():
        return "Project"

    @staticmethod
    def get_primary_key_name():
        return "project_id"


@dataclass
class ModelData(BaseSchema):
    model_id: int = None
    project_id: int = None
    model_name: str = None
    model_endpoint: str = None

    @staticmethod
    def get_table_name():
        return "Model"

    @staticmethod
    def get_primary_key_name():
        return "model_id"


@dataclass
class ResultData(BaseSchema):
    result_id: int = None
    model_id: int = None
    user_id: str = None
    question_version_id: int = None
    question_type: str = None
    result_score: int = None
    duration: int = None

    @staticmethod
    def get_table_name():
        return "Result"

    @staticmethod
    def get_primary_key_name():
        return "result_id"


@dataclass
class EvaluatorData(BaseSchema):
    evaluator_id: int = None
    employee_id: str = None
    password: str = None
    full_name: str = None
    email: str = None
    role: str = None
    company: str = None
    department: str = None

    @staticmethod
    def get_table_name():
        return "Evaluator"

    @staticmethod
    def get_primary_key_name():
        return "evaluator_id"


@dataclass
class OperationHistoryData(BaseSchema):
    operation_history_id: int = None
    user_id: str = None
    operation_type: str = None
    device_info: str = None
    ip_address: str = None
    description: str = None

    @staticmethod
    def get_table_name():
        return "OperationHistory"

    @staticmethod
    def get_primary_key_name():
        return "operation_history_id"


@dataclass
class ResultRecordData(BaseSchema):
    result_record_id: int = None
    result_id: int = None
    question_id: int = None
    model_response: str = None
    is_manual_evaluate: bool = None

    @staticmethod
    def get_table_name():
        return "ResultRecord"

    @staticmethod
    def get_primary_key_name():
        return "result_record_id"


@dataclass
class QuestionVersionData(BaseSchema):
    question_version_id: int = None
    question_version: int = None
    question_type: str = None

    @staticmethod
    def get_table_name():
        return "QuestionVersion"

    @staticmethod
    def get_primary_key_name():
        return "question_version_id"


@dataclass
class QuestionCategoryData(BaseSchema):
    question_category_id: int = None
    question_type: str = None
    type_prompt_content: str = None

    @staticmethod
    def get_table_name():
        return "QuestionCategory"

    @staticmethod
    def get_primary_key_name():
        return "question_category_id"


@dataclass
class QuestionData(BaseSchema):
    question_id: int = None
    question_version_id: int = None
    question_category_id: int = None
    question_content: str = None
    groundtruth_content: str = None
    groundtruth_type: str = None

    @staticmethod
    def get_table_name():
        return "Question"

    @staticmethod
    def get_primary_key_name():
        return "question_id"
