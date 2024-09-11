import json
import tempfile
from unittest.mock import patch

import pytest

from diarization_to_eaf.diarization_processor import DiarizationProcessor


@pytest.fixture
def valid_json_data():
    return [
        {"speaker": "SPEAKER_00", "start": 0.0, "end": 1.0},
        {"speaker": "SPEAKER_01", "start": 1.0, "end": 2.0},
        {"speaker": "SPEAKER_00", "start": 2.0, "end": 3.0},
        {"speaker": "SPEAKER_02", "start": 3.0, "end": 4.0},
    ]


@pytest.fixture
def json_file(valid_json_data):
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
        json.dump(valid_json_data, temp_file)
    return temp_file.name


def test_diarization_processor_init(json_file):
    processor = DiarizationProcessor(json_file)
    assert processor.json_file_path == json_file
    assert processor.diarization_data == []
    assert processor.operator_speaker == ""
    assert processor.caller_speakers == set()


def test_load_and_validate_data_valid(json_file):
    processor = DiarizationProcessor(json_file)
    processor.load_and_validate_data()
    assert len(processor.diarization_data) == 4


def test_load_and_validate_data_invalid():
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
        json.dump({"invalid": "structure"}, temp_file)

    processor = DiarizationProcessor(temp_file.name)
    with pytest.raises(ValueError, match="Invalid JSON structure"):
        processor.load_and_validate_data()


def test_process_diarization_data(json_file):
    processor = DiarizationProcessor(json_file)
    processor.load_and_validate_data()
    operator_segments, caller_segments = processor.process_diarization_data()

    assert len(operator_segments) == 2
    assert len(caller_segments) == 2
    assert all(segment['speaker'] == 'SPEAKER_00' for segment in operator_segments)
    assert all(segment['speaker'] != 'SPEAKER_00' for segment in caller_segments)


def test_process_diarization_data_no_data():
    processor = DiarizationProcessor("dummy.json")
    with pytest.raises(ValueError, match="No diarization data loaded"):
        processor.process_diarization_data()


def test_determine_speakers(json_file):
    processor = DiarizationProcessor(json_file)
    processor.load_and_validate_data()
    processor._determine_speakers()

    assert processor.operator_speaker == "SPEAKER_00"
    assert processor.caller_speakers == {"SPEAKER_01", "SPEAKER_02"}


def test_get_speaker_info(json_file):
    processor = DiarizationProcessor(json_file)
    processor.load_and_validate_data()
    processor._determine_speakers()

    speaker_info = processor.get_speaker_info()
    assert speaker_info['operator'] == "SPEAKER_00"
    assert set(speaker_info['callers']) == {"SPEAKER_01", "SPEAKER_02"}


@patch('diarization_to_eaf.diarization_processor.create_progress_bar')
def test_process_diarization_data_progress_bar(mock_progress_bar, json_file):
    mock_progress = mock_progress_bar.return_value

    processor = DiarizationProcessor(json_file)
    processor.load_and_validate_data()
    processor.process_diarization_data()

    mock_progress_bar.assert_called_once_with(4, "Processing diarization data")
    assert mock_progress.update.call_count == 4
    mock_progress.close.assert_called_once()
