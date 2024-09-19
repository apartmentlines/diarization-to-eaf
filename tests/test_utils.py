import json
import logging
import os
import tempfile
from unittest.mock import patch

import pytest

from diarization_to_eaf.utils import (
    setup_logging,
    check_file_exists,
    create_progress_bar,
    load_json_file,
)


def test_setup_logging(caplog):
    with caplog.at_level(logging.INFO):
        logger = setup_logging("INFO")
        logger.info("Test log message")
        assert "Test log message" in caplog.text


def test_setup_logging_debug(caplog):
    with caplog.at_level(logging.DEBUG):
        logger = setup_logging("DEBUG")
        logger.debug("Test debug message")
        assert "Test debug message" in caplog.text


def test_setup_logging_invalid_level():
    with pytest.raises(ValueError, match="Unknown level"):
        setup_logging("INVALID_LEVEL")


def test_check_file_exists():
    with tempfile.NamedTemporaryFile() as temp_file:
        assert check_file_exists(temp_file.name) is True
    assert check_file_exists("non_existent_file.txt") is False


def test_check_file_exists_error():
    with patch("os.path.isfile", side_effect=OSError("Mocked OSError")):
        with pytest.raises(OSError):
            check_file_exists("some_file.txt")


def test_create_progress_bar():
    progress_bar = create_progress_bar(100, "Test")
    assert progress_bar.total == 100
    assert progress_bar.desc == "Test"


def test_load_json_file():
    test_data = [{"speaker": "SPEAKER_00", "start": 0.0, "end": 1.0}]
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
        json.dump(test_data, temp_file)

    loaded_data = load_json_file(temp_file.name)
    assert loaded_data == test_data

    os.unlink(temp_file.name)


def test_load_json_file_invalid_json():
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
        temp_file.write("Invalid JSON")

    with pytest.raises(json.JSONDecodeError):
        load_json_file(temp_file.name)

    os.unlink(temp_file.name)


def test_load_json_file_file_not_found():
    with pytest.raises(OSError):
        load_json_file("non_existent_file.json")
