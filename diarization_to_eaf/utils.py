import json
import logging
import os
from typing import Any, Dict, Union

from tqdm import tqdm


def setup_logging(level: str = "INFO", name: str = "diarization_to_eaf") -> logging.Logger:
    """
    Set up logging for the application.

    :param level: The logging level (e.g., "DEBUG", "INFO", "WARNING")
    :type level: str
    :return: Configured logger
    :rtype: logging.Logger
    """
    # Create a new logger
    logger = logging.getLogger(name)
    logger.setLevel(level.upper())

    # Remove all handlers to avoid duplicate logging
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create a new handler
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Ensure the logger propagates messages to the root logger
    logger.propagate = True

    return logger


def check_file_exists(file_path: str) -> bool:
    """
    Check if a file exists at the given path.

    :param file_path: Path to the file
    :type file_path: str
    :return: True if the file exists, False otherwise
    :rtype: bool
    :raises OSError: If there's an error accessing the file system
    """
    try:
        return os.path.isfile(file_path)
    except OSError as e:
        logging.error(f"Error checking file existence: {e}")
        raise


def validate_json(json_data: Dict[str, Any]) -> bool:
    """
    Validate the structure of the diarization JSON data.

    :param json_data: The loaded JSON data
    :type json_data: Dict[str, Any]
    :return: True if the JSON is valid, False otherwise
    :rtype: bool
    """
    if not isinstance(json_data, list):
        return False

    required_keys = {"speaker", "start", "end"}

    for item in json_data:
        if not isinstance(item, dict):
            return False
        if not required_keys.issubset(item.keys()):
            return False
        if not isinstance(item["speaker"], str):
            return False
        if not isinstance(item["start"], (int, float)):
            return False
        if not isinstance(item["end"], (int, float)):
            return False
        if item["start"] >= item["end"]:
            return False

    return True


def create_progress_bar(total: int, desc: str = "Processing") -> tqdm:
    """
    Create a progress bar for long-running operations.

    :param total: Total number of items to process
    :type total: int
    :param desc: Description for the progress bar
    :type desc: str
    :return: A tqdm progress bar object
    :rtype: tqdm
    """
    return tqdm(total=total, desc=desc, unit="segments")


def load_json_file(file_path: str) -> Dict[str, Any]:
    """
    Load and parse a JSON file.

    :param file_path: Path to the JSON file
    :type file_path: str
    :return: Parsed JSON data
    :rtype: Dict[str, Any]
    :raises json.JSONDecodeError: If the JSON is invalid
    :raises OSError: If there's an error reading the file
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON in file {file_path}: {e}")
        raise
    except OSError as e:
        logging.error(f"Error reading file {file_path}: {e}")
        raise
