import yaml

from src.utils.logger import logger


def load_yaml(yaml_file):
    """Load config from yaml file

    Args:
        yaml_file (path): path for the yaml file

    Returns:
        dict: config load from yaml file
    """

    with open(yaml_file, "r") as f:
        data = yaml.load(f, Loader=yaml.Loader)

    logger.info(
        f"Done read yaml from path {yaml_file} and read api key from enviroment."
    )

    return data


yaml_data = load_yaml("config.yaml")
