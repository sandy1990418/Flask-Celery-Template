import logging
from abc import ABC, abstractmethod


def _enable_create(func):
    func._is_enable_create = True
    return func


class BaseDriver(ABC):
    def __init__(self, configs: dict):
        self.db_connection = self.connect(**configs["connect_args"])

    @abstractmethod
    def get_table_handler(self):
        pass

    @abstractmethod
    def connect(self, **kwargs):
        pass

    def _after_create_callback(self):
        pass

    def create_all_tables(self):
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if callable(attr) and getattr(attr, "_is_enable_create", False):
                attr()
        return self._after_create_callback()

    @_enable_create
    def create_project_table(self):
        """
        Create a Project table in the database.
        DB Attributes:
        -----
        project_id: INTEGER
        project_name: TEXT
        description: TEXT
        created_at: TIMESTAMP
        status: INTEGER
        """

        logging.info("Create Project Table...")

        creator = self.get_table_handler()

        creator.execute(
            """
            CREATE TABLE IF NOT EXISTS Project (
                project_id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_name TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status INTEGER NOT NULL
            );
            """
        )

    @_enable_create
    def create_model_table(self):
        """
        Create a Model table in the database.
        -----
        model_id: INTEGER
        project_id: INTEGER
        model_name: TEXT
        model_version: TEXT
        model_endpoint: TEXT
        exam_catogory: TEXT
        created_at: TIMESTAMP
        status: INTEGER
        """

        logging.info("Create Model Table...")

        creator = self.get_table_handler()

        creator.execute(
            """
            CREATE TABLE IF NOT EXISTS Model(
                model_id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                model_name TEXT NOT NULL,
                model_endpoint TEXT NOT NULL,
                exam_catogory TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status INTEGER NOT NULL,
                FOREIGN KEY (project_id) REFERENCES Project(project_id)
            );
            """
        )

    @_enable_create
    def create_result_table(self):
        """
        Create a Result table in the database.

        DB Attributes:
        -----
        result_id: INTEGER
        model_id: INTEGER
        user_id: TEXT
        question_version_id: INTEGER
        evaluation_type: TEXT
        result_score: INTEGER
        duration: INTEGER
        created_at: TIMESTAMP
        status: INTEGER
        """

        logging.info("Create Result Table...")

        creator = self.get_table_handler()

        creator.execute(
            """
            CREATE TABLE IF NOT EXISTS Result(
                result_id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_id INTEGER NOT NULL,
                user_id VARCHAR(8) NOT NULL,
                question_version_id INTEGER NOT NULL,
                evaluation_type TEXT,
                result_score INTEGER,
                duration INTEGER,  -- 假設是以秒單位
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status INTEGER NOT NULL,
                FOREIGN KEY (model_id) REFERENCES Model(model_id),
                FOREIGN KEY (user_id) REFERENCES Person(user_id),
                FOREIGN KEY (question_version_id) REFERENCES QuestionVersion(question_version_id)
            );
            """
        )

    @_enable_create
    def create_person_table(self):
        """
        Create a Person table in the database.

        DB Attributes:
        -----
        person_id: INTEGER
        user_id: VARCHAR
        password: TEXT
        name: TEXT
        email: TEXT
        created_at: TIMESTAMP
        status: INTEGER
        """

        logging.info("Create Person Table...")

        creator = self.get_table_handler()

        creator.execute(
            """
            CREATE TABLE IF NOT EXISTS Person (
                person_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id VARCHAR(8) NOT NULL,
                password TEXT NOT NULL,
                name TEXT NOT NULL,
                email TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status INTEGER NOT NULL
            );
            """
        )

    @_enable_create
    def create_operationhistory_table(self):
        """
        Create a OperationHistory table in the database.

        DB Attributes:
        -----
        operation_history_id: INTEGER
        user_id: VARCHAR
        operation_type: TEXT ["Create", "Update", "Delete", "Other"]
        device_info: TEXT
        ip_address: TEXT
        created_at: TIMESTAMP
        description: TEXT
        status: INTEGER
        """

        logging.info("Create OperationHistory Table...")

        creator = self.get_table_handler()

        creator.execute(
            """
            CREATE TABLE IF NOT EXISTS OperationHistory (
                operation_history_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id VARCHAR(8) NOT NULL,
                operation_type TEXT CHECK (operation_type IN ('Create', 'Update', 'Delete', 'Other')),
                device_info TEXT,
                ip_address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                description TEXT,
                status INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES Person(user_id)
            );
            """
        )

    @_enable_create
    def create_resultrecord_table(self):
        """
        Create a ResultRecord table in the database.

        DB Attributes:
        -----
        result_record_id: INTEGER
        result_id: INTEGER
        question_id: INTEGER
        model_response: TEXT
        created_at: TIMESTAMP
        status: INTEGER
        """

        logging.info("Create ResponseRecord Table...")

        creator = self.get_table_handler()

        creator.execute(
            """
            CREATE TABLE IF NOT EXISTS ResultRecord (
                result_record_id INTEGER PRIMARY KEY AUTOINCREMENT,
                result_id INTEGER NOT NULL,
                question_id INTEGER NOT NULL,
                model_response TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status INTEGER NOT NULL,
                FOREIGN KEY (result_id) REFERENCES Result(result_id),
                FOREIGN KEY (question_id) REFERENCES Question(question_id)
            );
            """
        )

    @_enable_create
    def create_question_table(self):
        """
        Create a Question table in the database.

        DB Attributes:
        -----
        question_id: INTEGER
        question_version_id: INTEGER
        question_category: TEXT
        question_content: TEXT
        groundtruth_content: TEXT
        groundtruth_set: TEXT
        groundtruth_type: TEXT
        created_at: TIMESTAMP
        status: INTEGER
        """

        logging.info("Create Question Table...")

        creator = self.get_table_handler()

        creator.execute(
            """
            CREATE TABLE IF NOT EXISTS Question (
                question_id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_version_id INTEGER NOT NULL,
                question_category TEXT NOT NULL,
                question_content TEXT NOT NULL,
                groundtruth_content TEXT,
                groundtruth_set TEXT NOT NULL,
                groundtruth_type TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status INTEGER NOT NULL
            );
            """
        )
