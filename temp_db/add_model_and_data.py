from typing import List, Tuple

from drivers.sqlite_driver import SQLiteDriver

from src.utils.load_yaml import yaml_data


def insert_model_data():
    repo = SQLiteDriver(yaml_data["sqlite"])
    cursor = repo.get_table_handler()
    cursor.execute("PRAGMA foreign_keys = OFF;")

    models: List[Tuple] = [
        (1, "gpt-4o", "https://api.openai.com/v1/chat/completions", 1),
        (1, "gpt-4o-mini", "https://api.openai.com/v1/chat/completions", 1),
    ]

    cursor.executemany(
        """
    INSERT INTO Model
        (project_id, model_name, model_endpoint, status)
    VALUES (?, ?, ?, ?)
    """,
        models,
    )

    repo._after_create_callback()


def transform_question_format(question):
    new_question = f"{question['Question']}, A:{question['A']}, B:{question['B']}, C:{question['C']}, D:{question['D']}"

    return {
        "Question": new_question,
        "Answer": question["Answer"],
        "Subject": question["Subject"],
    }


def repare_for_insert(question):
    question_set = []

    for idx in question["test"]:
        question_set.append(
            (
                1,
                idx["Question"],
                idx["Answer"],
                "Classfication",
                '["A", "B", "C", "D"]',
                idx["Subject"],
                1,
            )
        )

    return question_set


def insert_question_data():
    repo = SQLiteDriver(yaml_data["sqlite"])
    cursor = repo.get_table_handler()
    cursor.execute("PRAGMA foreign_keys = OFF;")

    from datasets import load_dataset

    ds = load_dataset("openai/MMMLU", "ZH_CN")

    transformed_dataset = ds.map(transform_question_format)
    question_set = repare_for_insert(transformed_dataset)

    cursor.executemany(
        """
        INSERT INTO Question
            (question_version_id,
            question_content,
            groundtruth_content,
            groundtruth_type,
            groundtruth_set,
            question_category,
            status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        question_set,
    )

    repo._after_create_callback()


if __name__ == "__main__":
    insert_model_data()
    insert_question_data()
