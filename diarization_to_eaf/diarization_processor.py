from typing import List, Dict, Any, Tuple

from diarization_to_eaf.utils import load_json_file, create_progress_bar, setup_logging


class DiarizationProcessor:
    """
    A class to process speaker diarization data from JSON format.
    """

    def __init__(self, json_file_path: str, log_level: str = "INFO"):
        """
        Initialize the DiarizationProcessor.

        :param json_file_path: Path to the JSON file containing diarization data
        :type json_file_path: str
        """
        self.json_file_path = json_file_path
        self.diarization_data: List[Dict[str, Any]] = []
        self.operator_speaker: str = ""
        self.caller_speakers: set = set()
        self.logger = setup_logging(log_level, __class__.__name__)
        self.logger.debug(
            f"Initialized DiarizationProcessor with file: {json_file_path}"
        )

    def load_and_validate_data(self) -> None:
        """
        Load the JSON file and validate its structure.

        :raises ValueError: If the JSON structure is invalid
        :raises OSError: If there's an error reading the file
        :raises json.JSONDecodeError: If the JSON is invalid
        """
        self.logger.debug("Loading and validating diarization data")
        data = load_json_file(self.json_file_path)
        if not data or not self._validate_json(data):
            raise ValueError("Invalid JSON structure in the diarization data")
        self.diarization_data = data["output"]["diarization"]
        self.logger.info(
            f"Successfully loaded and validated data from {self.json_file_path}"
        )

    def _validate_json(self, data: Dict[str, Any]) -> bool:
        """
        Validate the structure of the diarization JSON data.

        :param data: The loaded JSON data
        :type data: Dict[str, Any]
        :return: True if the JSON is valid, False otherwise
        :rtype: bool
        """
        if not isinstance(data, dict):
            return False
        if "jobId" not in data or "status" not in data or "output" not in data:
            return False
        if not isinstance(data["output"], dict) or "diarization" not in data["output"]:
            return False
        if not isinstance(data["output"]["diarization"], list):
            return False
        for segment in data["output"]["diarization"]:
            if not isinstance(segment, dict):
                return False
            if (
                "speaker" not in segment
                or "start" not in segment
                or "end" not in segment
            ):
                return False
            if not isinstance(segment["speaker"], str):
                return False
            if not isinstance(segment["start"], (int, float)) or not isinstance(
                segment["end"], (int, float)
            ):
                return False
            if segment["start"] >= segment["end"]:
                return False
        return True

    def process_diarization_data(
        self,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Process the diarization data to separate Operator and Caller segments.

        :return: A tuple containing two lists of diarization segments (Operator, Caller)
        :rtype: Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]
        """
        self.logger.debug("Processing diarization data")
        if not self.diarization_data:
            raise ValueError(
                "No diarization data loaded. Call load_and_validate_data() first."
            )

        self._determine_speakers()

        operator_segments = []
        caller_segments = []

        progress_bar = create_progress_bar(
            len(self.diarization_data), "Processing diarization data"
        )

        for segment in self.diarization_data:
            if segment["speaker"] == self.operator_speaker:
                operator_segments.append(segment)
            else:
                caller_segments.append(segment)
            progress_bar.update(1)

        progress_bar.close()

        self.logger.debug(
            f"Processed {len(self.diarization_data)} diarization segments"
        )
        return operator_segments, caller_segments

    def _determine_speakers(self) -> None:
        """
        Determine the Operator speaker and Caller speakers based on the first segment.
        """
        self.logger.debug("Determining speakers")
        if not self.diarization_data:
            raise ValueError("No diarization data available")

        self.operator_speaker = self.diarization_data[0]["speaker"]
        self.caller_speakers = set(
            segment["speaker"]
            for segment in self.diarization_data
            if segment["speaker"] != self.operator_speaker
        )

        self.logger.debug(f"Identified Operator speaker: {self.operator_speaker}")
        self.logger.debug(
            f"Identified Caller speakers: {', '.join(self.caller_speakers)}"
        )

    def get_speaker_info(self) -> Dict[str, Any]:
        """
        Get information about the identified speakers.

        :return: A dictionary containing speaker information
        :rtype: Dict[str, Any]
        """
        return {
            "operator": self.operator_speaker,
            "callers": list(self.caller_speakers),
        }
