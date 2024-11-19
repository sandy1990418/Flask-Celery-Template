from abc import ABC
from collections import defaultdict
from typing import Dict, List, Set, Tuple

import pandas as pd

from src.models.db_client import DatabaseClient, Sqlite3Client
from src.models.db_schema import BaseSchema, ModelData, ProjectData, QuestionData
from src.utils.logger import logger


class BaseRepository(ABC):
    """Definition of Repository"""

    def __init__(self, db_client: DatabaseClient):
        self.db_client = db_client

        # To Record User Operations
        self.metadata = {
            "LastOperation": {
                "OperationType": None,
                "OperationTable": None,
                "OperationID": None,
                "Status": None,
            }
        }

    @property
    def all_tables(self) -> Set[str]:
        return {
            table_schema.get_table_name()
            for table_schema in BaseSchema.__subclasses__()
        }

    @property
    def table_data(self) -> Dict[str, BaseSchema]:
        return {
            table_schema.get_table_name(): table_schema
            for table_schema in BaseSchema.__subclasses__()
        }

    @classmethod
    def from_config(cls, config: str, **kwargs):
        if config["active_database"] == "sqlite":
            client = Sqlite3Client(
                db_path=config[config["active_database"]]["connect_args"]["database"]
            )
        else:
            raise NotImplementedError(
                f"The DB '{config['active_database']}' is not yet implemented. "
                f"Currently, we only support the features: {list(config.keys())}. "
                "Please check back later for updates or choose from the supported options."
            )

        return cls(db_client=client, **kwargs)

    def _record_user_operations(self, **kwargs):
        self.metadata["LastOperation"] = {**kwargs}


class SimplifiedRepository(BaseRepository):
    def select_all(self, db_schema: BaseSchema) -> List[BaseSchema]:
        results = defaultdict()
        table_name = db_schema.get_table_name()

        try:
            logger.debug(f"Do select all SQL command with {table_name}...")

            if table_name not in self.all_tables:
                raise ValueError(f"Table {table_name} is not in Database.")

            results = self.db_client.table_handler.execute(
                f"""SELECT * FROM {table_name}"""
            ).fetchall()

            results = self.db_client.process_to_dataclass(
                align_dataclass=self.table_data[table_name], data=results
            )
            status = "Success"
        except Exception as e:
            status = "Failed"
            logger.error(e)
        finally:
            self._record_user_operations(
                OperationType="select_all", OperationTable=table_name, Status=status
            )
            return results

    def add(self, schema_data: BaseSchema) -> None:
        table_name = schema_data.get_table_name()
        try:
            logger.debug(f"Insert data into {table_name} table...")
            schema_data.status = schema_data.status or 1  # default
            # get all variable which fit Database Schema
            variable_data = schema_data.__dict__
            variable_data.pop(schema_data.get_primary_key_name())
            variable_data.pop("created_at")
            attributes = ", ".join(i for i in variable_data)
            values = ", ".join("?" for _ in variable_data)
            sql_command = f"INSERT INTO {table_name} ({attributes}) VALUES ({values});"
            self.db_client.table_handler.execute(
                sql_command, tuple(variable_data.values())
            )
            self.db_client.conn.commit()
            record_id = self.db_client.table_handler.lastrowid
            status = "Success"
            logger.debug(f"{schema_data.get_table_name()} insert successfully.")
        except Exception as e:
            record_id = None
            status = "Failed"
            logger.error(e)
        finally:
            self._record_user_operations(
                OperationType="add",
                OperationTable=table_name,
                OperationID=record_id,
                Status=status,
            )

    def update(self, schema_data: BaseSchema) -> None:
        table_name = schema_data.get_table_name()

        try:
            logger.debug(f"Update data into {table_name} table...")
            update_data = {
                key: value for key, value in schema_data.__dict__.items() if value
            }
            update_condition_name = schema_data.get_primary_key_name()
            update_condition_value = update_data.pop(update_condition_name)
            attributes = ", ".join(f"{i} = ?" for i in update_data.keys())
            sql_command = f"UPDATE {table_name} SET {attributes} WHERE {update_condition_name} = ?;"
            self.db_client.table_handler.execute(
                sql_command, tuple(update_data.values()) + (update_condition_value,)
            )
            self.db_client.conn.commit()
            status = "Success"
            logger.debug(f"{table_name} update successfully.")
        except Exception as e:
            status = "Failed"
            logger.error(e)
        finally:
            self._record_user_operations(
                OperationType="update",
                OperationTable=table_name,
                Status=status,
            )

    def delete(self, schema_data: BaseSchema) -> None:
        table_name = schema_data.get_table_name()

        try:
            logger.debug(f"Delete {table_name} table data...")
            delete_data = schema_data.__dict__
            delete_condition_name = schema_data.get_primary_key_name()
            delete_condition_value = delete_data.get(delete_condition_name)
            sql_command = (
                f"UPDATE {table_name} SET status = 0 WHERE {delete_condition_name} = ?;"
            )
            self.db_client.table_handler.execute(sql_command, (delete_condition_value,))
            self.db_client.conn.commit()
            status = "Success"
            logger.debug(f"{table_name} data delete successfully.")
        except Exception as e:
            status = "Failed"
            logger.error(e)
        finally:
            self._record_user_operations(
                OperationType="delete",
                OperationTable=table_name,
                Status=status,
            )


class ResultRepositroy(SimplifiedRepository):
    def get_question(
        self, question_version_id: int, question_category: str
    ) -> List[BaseSchema]:
        results = []

        try:
            logger.debug("Do filter SQL command with table Question...")

            sql_command = """SELECT * FROM Question WHERE question_version_id = ? AND question_category = ?;"""

            results = self.db_client.table_handler.execute(
                sql_command,
                (
                    question_version_id,
                    question_category,
                ),
            ).fetchall()

            results = self.db_client.process_to_dataclass(
                align_dataclass=self.table_data["Question"], data=results
            )
            status = "Success"
        except Exception as e:
            status = "Failed"
            logger.error(e)
        finally:
            self._record_user_operations(
                OperationType="get_question",
                OperationTable="Question",
                Status=status,
            )
            return results

    def get_question_version_id(
        self, question_category: str, question_version: int
    ) -> List[BaseSchema]:
        results = []

        try:
            logger.debug("Do filter SQL command with table QuestionVersion...")

            sql_command = """SELECT * FROM Question WHERE question_category = ? AND question_version_id = ?;"""

            results = self.db_client.table_handler.execute(
                sql_command, (question_category, question_version)
            ).fetchall()

            results = self.db_client.process_to_dataclass(
                align_dataclass=self.table_data["Question"], data=results
            )
            status = "Success"
        except Exception as e:
            status = "Failed"
            logger.error(e)
        finally:
            self._record_user_operations(
                OperationType="get_question",
                OperationTable="Question",
                Status=status,
            )
            return results

    def get_evaluation_version(self) -> dict:
        result = defaultdict(list)
        question_version_data: List[QuestionData] = self.select_all(QuestionData)

        for each_data in question_version_data:
            result[each_data.question_category].append(each_data.question_version_id)
        return result

    def get_latest_evaluation_result_by_model(self, model_id: int) -> bool:
        results = []
        try:
            sql_command = "SELECT * FROM Result WHERE model_id = ? ORDER BY created_at DESC LIMIT 1"

            results = self.db_client.table_handler.execute(
                sql_command, (model_id,)
            ).fetchall()

            results = self.db_client.process_to_dataclass(
                align_dataclass=self.table_data["Result"], data=results
            )

            status = "Success"

        except Exception as e:
            status = "Failed"
            logger.error(e)
        finally:
            self._record_user_operations(
                OperationType="is_model_locked",
                OperationTable="Result",
                Status=status,
            )
            return results


class ReportsRepository(SimplifiedRepository):
    def get_project_model_data(self) -> Tuple[List[BaseSchema], List[BaseSchema], str]:
        project_data = self.select_all(ProjectData)
        model_data = self.select_all(ModelData)
        return project_data, model_data, "project_id"

    def get_project_history_data_by_id(self, project_id: int) -> pd.DataFrame:
        results = pd.DataFrame()

        try:
            logger.debug("Get project history...")

            sql_command = """
            SELECT EM.model_name,
                   EM.model_endpoint,
                   EM.exam_catogory,
                   ER.question_version_id,
                   ER.evaluation_type ,
                   ER.result_score ,
                   ER.duration ,
                   ER.created_at ,
                   ER.status
            FROM Result AS ER
            JOIN Model AS EM ON ER.model_id = EM.model_id
            WHERE EM.project_id = ?;
            """

            tmp = self.db_client.table_handler.execute(
                sql_command, (project_id,)
            ).fetchall()

            results = pd.DataFrame(
                tmp,
                columns=[
                    "Model Name",
                    "Model Endpoint",
                    "Evaluation Catogories",
                    "Question Version",
                    "Evaluation Type",
                    "Evaluation Score",
                    "Durations",
                    "Date",
                    "status",
                ],
            )

            status = "Success"
        except Exception as e:
            status = "Failed"
            logger.error(e)
        finally:
            self._record_last_metadata(
                OperationType="select_all",
                OperationTable=["Project", "ExamineeModel"],
                Status=status,
            )
            return results
