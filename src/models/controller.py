from typing import Any, List

import pandas as pd
from flask import Request

from src.models.db_schema import BaseSchema, PersonData
from src.models.repository import (
    ReportsRepository,
    ResultRepositroy,
    SimplifiedRepository,
)
from src.utils.data_handler import BaseHandler, RequestHandler
from src.utils.load_yaml import yaml_data as CONFIG
from src.utils.logger import logger

EXPERIMENT_DATA_LENGTH = 3


class BasicController:
    def __init__(self, request_handler: SimplifiedRepository):
        self.request_handler = request_handler
        self.repository = SimplifiedRepository.from_config(CONFIG)

    def add_data(self, request_data: Request) -> None:
        db_schema = self.request_handler.process_data(request_data)
        return self.repository.add(db_schema)

    def update_data(self, request_data: Request) -> None:
        db_schema = self.request_handler.process_data(request_data)
        return self.repository.update(db_schema)

    def delete_data(self, request_data: Request) -> None:
        db_schema = self.request_handler.process_data(request_data)
        return self.repository.delete(db_schema)

    @staticmethod
    def get_all_data(db_schema: BaseSchema) -> List[BaseSchema]:
        repository = SimplifiedRepository.from_config(CONFIG)
        return repository.select_all(db_schema)


class EvaluationController(BasicController):
    def __init__(self, request_handler: BaseHandler = None):
        self.repository = ResultRepositroy.from_config(CONFIG)
        self.request_handler = request_handler

    def is_model_locked(self, model_id: int) -> bool:
        latest_model_record: List[
            BaseSchema
        ] = self.repository.get_latest_evaluation_result_by_model(model_id=model_id)

        if latest_model_record:
            if latest_model_record[0].status == 3 or latest_model_record[0].status == 4:
                logger.warning(
                    f"The  model with ID {model_id} is currently in use by another process. "
                    "Please try again later or contact the administrator if the issue persists."
                )
                return True

        return False

    def is_evaluator_exist(self, request_data: Request) -> bool:
        request_handler = self.request_handler or RequestHandler(
            align_dataclass=PersonData
        )

        db_schema = request_handler.process_data(request_data)

        all_db_data = self.repository.select_all(db_schema)

        for db_data in all_db_data:
            if db_data.user_id == db_schema.user_id:
                return True
        return False

    def is_login_success(self, request_data: Request) -> bool:
        request_handler = self.request_handler or RequestHandler(
            align_dataclass=PersonData
        )

        db_schema = request_handler.process_data(request_data)

        all_db_data = self.repository.select_all(db_schema)

        for db_data in all_db_data:
            if (
                db_data.user_id == db_schema.user_id
                and db_data.password == db_schema.password
            ):
                return True

        return False

    def get_question_version_id(
        self, evaluation_type: str, question_version: int
    ) -> int:
        question_version_data = self.repository.get_question_version_id(
            question_category=evaluation_type, question_version=question_version
        )

        if len(question_version_data) == 0:
            raise ValueError(
                f"Data Missing Error: Evaluation Type {evaluation_type}, Question Version {question_version}"
            )

        question_version_id = int(question_version_data[0].question_version_id)
        return question_version_id

    def get_question(
        self, question_version_id: int, question_category: str
    ) -> List[BaseSchema]:
        all_questions = self.repository.get_question(
            question_version_id, question_category
        )
        return all_questions[:EXPERIMENT_DATA_LENGTH]

    def get_evaluation_version(self):
        return self.repository.get_evaluation_version()

    def prepare_exam(self, request_data: Request, session: Any) -> List[dict]:
        test_papers: List[dict] = []
        try:
            json_data = request_data.get_json()
            for each_exam in json_data["exam_info"]:
                evaluation_result = {
                    "model_id": json_data["model_id"],
                    "user_id": session["user_basic_info"]["user_id"],
                    "question_version_id": "TBD",
                    "evaluation_type": each_exam["topic"],
                    "status": 3,  # 評測正在進行中
                }

                test_papers.append(
                    {
                        "result": evaluation_result,
                        "evaluation_type": each_exam["topic"],
                        "version": each_exam["version"],
                        "model_id": json_data["model_id"],
                        "model_name": json_data["model_name"],
                        "model_version": json_data["model_version"],
                        "model_endpoint": json_data["model_endpoint"],
                    }
                )
        except Exception as e:
            logger.error(f"Prepare Exam Error: {e}")
        finally:
            return test_papers


class ReportsController:
    @staticmethod
    def get_project_history_data_by_id(project_id: int) -> pd.DataFrame:
        repository = ReportsRepository.from_config(CONFIG)
        project_history = repository.get_project_history_data_by_id(
            project_id=project_id
        )
        return project_history

    @staticmethod
    def get_project_model_data():
        repository = ReportsRepository.from_config(CONFIG)
        project_data, model_data, foreigner_key = repository.get_project_model_data()

        for project in project_data:
            project.include_child = []
            for model in model_data:
                if (
                    model.__dict__.get(foreigner_key)
                    == project.__dict__.get(foreigner_key)
                    and model.__dict__.get("status") == 1
                ):
                    project.include_child.append(model)

        return project_data

    @staticmethod
    def get_manual_quesiton_data(evaluation_result_ids: List[int]) -> pd.DataFrame:
        repository = ReportsRepository.from_config(CONFIG)
        manual_quesiton_data = repository.get_manual_quesiton_data_by_id(
            evaluation_result_ids=evaluation_result_ids
        )
        return manual_quesiton_data
