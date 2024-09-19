import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from diarization_to_eaf.diarization_processor import DiarizationProcessor
from diarization_to_eaf.main import parse_arguments, process_file, main


@pytest.fixture
def valid_json_data():
    return {
        "jobId": "d22f9945-90a1-40d0-977d-4eccc3d6dc32",
        "status": "succeeded",
        "output": {
            "diarization": [
                {"speaker": "SPEAKER_01", "start": 0.645, "end": 4.485},
                {"speaker": "SPEAKER_00", "start": 6.725, "end": 7.645},
            ]
        },
    }


@pytest.fixture
def json_file(valid_json_data):
    with tempfile.NamedTemporaryFile(
        mode="w", delete=False, suffix=".json"
    ) as temp_file:
        json.dump(valid_json_data, temp_file)
    return temp_file.name


def test_parse_arguments():
    with patch(
        "sys.argv",
        [
            "script.py",
            "--input-file",
            "input.json",
            "--output-dir",
            "output",
            "--debug",
        ],
    ):
        args = parse_arguments()
        assert args.input_file == "input.json"
        assert args.output_dir == "output"
        assert args.input_dir is None

    with patch(
        "sys.argv",
        ["script.py", "--input-dir", "input_dir", "--output-dir", "output", "--debug"],
    ):
        args = parse_arguments()
        assert args.input_dir == "input_dir"
        assert args.output_dir == "output"
        assert args.input_file is None


@patch("diarization_to_eaf.main.DiarizationProcessor")
@patch("diarization_to_eaf.main.EAFGenerator")
def test_process_file(mock_eaf_generator, mock_diarization_processor, json_file):
    mock_processor = MagicMock()
    mock_processor.process_diarization_data.return_value = ([], [])
    mock_diarization_processor.return_value = mock_processor

    mock_generator = MagicMock()
    mock_eaf_generator.return_value = mock_generator

    input_path = Path(json_file)
    output_path = Path("output.eaf")
    process_file(input_path, output_path, None, "INFO")

    mock_diarization_processor.assert_called_once_with(str(input_path), "INFO")
    mock_processor.load_and_validate_data.assert_called_once()
    mock_processor.process_diarization_data.assert_called_once()
    mock_eaf_generator.assert_called_once_with(str(input_path), [], [], None, "INFO")
    mock_generator.generate_eaf.assert_called_once()
    mock_generator.write_to_file.assert_called_once_with(output_path)


@patch("diarization_to_eaf.main.process_file")
@patch("diarization_to_eaf.main.check_file_exists")
def test_main_single_file(mock_check_file_exists, mock_process_file):
    mock_check_file_exists.return_value = True
    with patch(
        "sys.argv",
        ["script.py", "--input-file", "input.json", "--output-dir", "output"],
    ):
        main()
        mock_process_file.assert_called_once()


@patch("diarization_to_eaf.main.process_file")
@patch("pathlib.Path.is_dir")
@patch("pathlib.Path.glob")
def test_main_directory(mock_glob, mock_is_dir, mock_process_file):
    mock_is_dir.return_value = True
    mock_glob.return_value = [Path("file1.json"), Path("file2.json")]
    with patch(
        "sys.argv", ["script.py", "--input-dir", "input_dir", "--output-dir", "output"]
    ):
        main()
        assert mock_process_file.call_count == 2


@patch("diarization_to_eaf.main.check_file_exists")
def test_main_file_not_found(mock_check_file_exists):
    mock_check_file_exists.return_value = False
    with patch("sys.argv", ["script.py", "--input-file", "nonexistent.json"]):
        with pytest.raises(SystemExit):
            main()


@patch("pathlib.Path.is_dir")
def test_main_directory_not_found(mock_is_dir):
    mock_is_dir.return_value = False
    with patch("sys.argv", ["script.py", "--input-dir", "nonexistent_dir"]):
        with pytest.raises(SystemExit):
            main()


def test_get_speaker_info(json_file):
    processor = DiarizationProcessor(json_file)
    processor.load_and_validate_data()
    processor.process_diarization_data()
    speaker_info = processor.get_speaker_info()

    assert "operator" in speaker_info
    assert "callers" in speaker_info
    assert isinstance(speaker_info["callers"], list)


@pytest.mark.parametrize(
    "invalid_data",
    [
        {},  # Empty dict
        {"jobId": "123", "status": "succeeded"},  # Missing output
        {"jobId": "123", "status": "succeeded", "output": {}},  # Missing diarization
        {
            "jobId": "123",
            "status": "succeeded",
            "output": {"diarization": [{"invalid": "data"}]},
        },  # Missing required keys
        {
            "jobId": "123",
            "status": "succeeded",
            "output": {
                "diarization": [
                    {"speaker": "SPEAKER_00", "start": "invalid", "end": 1.0}
                ]
            },
        },  # Invalid start time
    ],
)
def test_load_and_validate_data_error(invalid_data):
    with tempfile.NamedTemporaryFile(
        mode="w", delete=False, suffix=".json"
    ) as temp_file:
        json.dump(invalid_data, temp_file)

    processor = DiarizationProcessor(temp_file.name)

    with pytest.raises(ValueError):
        processor.load_and_validate_data()

    os.unlink(temp_file.name)
