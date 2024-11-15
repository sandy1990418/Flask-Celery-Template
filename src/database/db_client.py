import sqlite3
from abc import ABC, abstractmethod
from typing import Any, List

from .db_schema import BaseSchema


class DatabaseClient(ABC):
    def __init__(self, db_path, **kwargs):
        self.db_path = db_path
        self.conn = self.connect()
        self.table_handler = self.get_table_handler()

    @abstractmethod
    def connect(self) -> bool:
        raise NotImplementedError("Please Implement this method of `DatabaseClient`.")

    @abstractmethod
    def close_connection(self) -> bool:
        raise NotImplementedError("Please Implement this method of `DatabaseClient`.")

    @abstractmethod
    def get_table_handler(self):
        pass

    @abstractmethod
    def process_to_dataclass(self, align_dataclass: BaseSchema, data: Any):
        pass

    @abstractmethod
    def process_to_dict(self, data: Any):
        pass


class Sqlite3Client(DatabaseClient):
    def connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def close_connection(self):
        self.conn.close()

    def get_table_handler(self):
        return self.conn.cursor()

    def process_to_dataclass(
        self, align_dataclass: BaseSchema, data: List[sqlite3.Row]
    ) -> List[BaseSchema]:
        return [align_dataclass(**row) for row in data]

    def process_to_dict(self, data: List[sqlite3.Row]) -> List[dict]:
        return [dict(row) for row in data]
