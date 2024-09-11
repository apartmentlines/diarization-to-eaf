import os
import tempfile
from unittest.mock import patch
import pytest
from lxml import etree

from diarization_to_eaf.eaf_generator import EAFGenerator


@pytest.fixture
def sample_segments():
    operator_segments = [
        {"speaker": "SPEAKER_00", "start": 0.0, "end": 1.0},
        {"speaker": "SPEAKER_00", "start": 2.0, "end": 3.0},
    ]
    caller_segments = [
        {"speaker": "SPEAKER_01", "start": 1.0, "end": 2.0},
        {"speaker": "SPEAKER_02", "start": 3.0, "end": 4.0},
    ]
    return operator_segments, caller_segments


@pytest.fixture
def eaf_generator(sample_segments):
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp_file:
        temp_file_path = temp_file.name

    operator_segments, caller_segments = sample_segments
    return EAFGenerator(temp_file_path, operator_segments, caller_segments)


def test_init(eaf_generator, sample_segments):
    operator_segments, caller_segments = sample_segments
    assert eaf_generator.operator_segments == operator_segments
    assert eaf_generator.caller_segments == caller_segments
    assert eaf_generator.root is None
    assert eaf_generator.time_order is None
    assert eaf_generator.time_slot_map == {}


def test_generate_eaf(eaf_generator):
    eaf_generator.generate_eaf()
    assert eaf_generator.root is not None
    assert eaf_generator.root.tag == "ANNOTATION_DOCUMENT"
    assert eaf_generator.time_order is not None


def test_create_header(eaf_generator):
    eaf_generator.generate_eaf()
    header = eaf_generator.root.find("HEADER")
    assert header is not None
    assert header.get("TIME_UNITS") == "milliseconds"

    media_descriptor = header.find("MEDIA_DESCRIPTOR")
    assert media_descriptor is not None
    assert media_descriptor.get("MIME_TYPE") == "audio/x-wav"

    property_elem = header.find("PROPERTY")
    assert property_elem is not None
    assert property_elem.get("NAME") == "URN"
    assert property_elem.text.startswith("urn:nl-mpi-tools-elan-eaf:")


def test_create_time_order(eaf_generator):
    eaf_generator.generate_eaf()
    time_slots = eaf_generator.time_order.findall("TIME_SLOT")
    assert len(time_slots) == 8  # 2 for each segment (start and end)

    # Check if time slots are in order and have correct values
    for i, slot in enumerate(time_slots):
        assert slot.get("TIME_SLOT_ID") == f"ts{i+1}"
        assert slot.get("TIME_VALUE") in ["0", "1000", "2000", "3000", "4000"]


def test_create_tiers(eaf_generator):
    eaf_generator.generate_eaf()
    tiers = eaf_generator.root.findall("TIER")
    assert len(tiers) == 2

    operator_tier = eaf_generator.root.find("TIER[@TIER_ID='Operator']")
    caller_tier = eaf_generator.root.find("TIER[@TIER_ID='Caller']")

    assert operator_tier is not None
    assert caller_tier is not None

    operator_annotations = operator_tier.findall(".//ALIGNABLE_ANNOTATION")
    caller_annotations = caller_tier.findall(".//ALIGNABLE_ANNOTATION")

    assert len(operator_annotations) == 2
    assert len(caller_annotations) == 2


def test_create_linguistic_types(eaf_generator):
    eaf_generator.generate_eaf()
    linguistic_types = eaf_generator.root.findall("LINGUISTIC_TYPE")
    assert len(linguistic_types) == 1
    assert linguistic_types[0].get("LINGUISTIC_TYPE_ID") == "default-lt"


def test_create_constraints(eaf_generator):
    eaf_generator.generate_eaf()
    constraints = eaf_generator.root.findall("CONSTRAINT")
    assert len(constraints) == 4


@patch('uuid.uuid4')
def test_write_to_file(mock_uuid, eaf_generator, tmpdir):
    mock_uuid.return_value = "test-uuid"
    eaf_generator.generate_eaf()
    output_path = eaf_generator.write_to_file()

    assert os.path.exists(output_path)
    assert output_path.endswith('.eaf')

    # Validate the content of the file
    tree = etree.parse(output_path)
    root = tree.getroot()

    assert root.tag == "ANNOTATION_DOCUMENT"
    assert root.find(".//PROPERTY[@NAME='URN']").text == "urn:nl-mpi-tools-elan-eaf:test-uuid"


@pytest.mark.parametrize("json_path, expected_relative_path, expected_media_url", [
    ("file.json", "./file.wav", "file://file.wav"),
    ("subdir/file.json", "./subdir/file.wav", "file://subdir/file.wav"),
    ("file1.json", "./file1.wav", "file://file1.wav"),
    ("subdir1/subdir2/file.json", "./subdir1/subdir2/file.wav", "file://subdir1/subdir2/file.wav"),
])
def test_get_media_urls(eaf_generator, json_path, expected_relative_path, expected_media_url, mocker):
    eaf_generator.json_file_path = json_path
    mocker.patch('os.path.exists', return_value=True)

    relative_url = eaf_generator._get_relative_media_url()
    assert relative_url == expected_relative_path

    media_url = eaf_generator._get_media_url()
    assert media_url == expected_media_url

@pytest.mark.parametrize("json_path", [
    "file.json",
    "subdir/file.json",
])
def test_get_media_urls_file_not_exists(eaf_generator, json_path, mocker):
    eaf_generator.json_file_path = json_path
    mocker.patch('os.path.exists', return_value=False)

    relative_url = eaf_generator._get_relative_media_url()
    assert relative_url == ""

    media_url = eaf_generator._get_media_url()
    assert media_url == ""


@patch('diarization_to_eaf.eaf_generator.create_progress_bar')
def test_progress_bars(mock_progress_bar, eaf_generator):
    mock_progress = mock_progress_bar.return_value
    eaf_generator.generate_eaf()

    # Check if progress bars were created for time slots and annotations
    assert mock_progress_bar.call_count == 3
    assert mock_progress.update.call_count == 12  # 8 time slots + 4 annotations
    assert mock_progress.close.call_count == 3
