import sqlite3

from drivers.base_driver import BaseDriver


class SQLiteDriver(BaseDriver):
    def __init__(self, configs):
        super().__init__(configs)

        self._enable_foreign_key()

    def get_table_handler(self):
        return self.db_connection.cursor()

    def _after_create_callback(self):
        self.db_connection.commit()

    def _enable_foreign_key(self):
        cursor = self.db_connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")

    def connect(self, database: str, **kwargs):
        return sqlite3.connect(database=database, **kwargs)
