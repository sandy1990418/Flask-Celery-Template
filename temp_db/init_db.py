from drivers.sqlite_driver import SQLiteDriver

from src.utils.load_yaml import yaml_data

if __name__ == "__main__":
    repo = SQLiteDriver(yaml_data["sqlite"])
    repo.create_all_tables()
