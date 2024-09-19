import os
import uuid
from typing import List, Dict, Any, Optional
from lxml import etree
from datetime import datetime
from pathlib import Path

from diarization_to_eaf.utils import create_progress_bar, setup_logging


class EAFGenerator:
    """
    A class to generate ELAN Annotation Format (EAF) files from diarization data.
    """

    def __init__(
        self,
        json_file_path: str,
        operator_segments: List[Dict[str, Any]],
        caller_segments: List[Dict[str, Any]],
        media_dir: Optional[Path] = None,
        log_level: str = "INFO",
    ):
        """
        Initialize the EAFGenerator.

        :param json_file_path: Path to the original JSON file (used for naming the output)
        :param operator_segments: List of operator speech segments
        :param caller_segments: List of caller speech segments
        :param media_dir: Optional path to the directory containing media files
        :param log_level: Logging level
        """
        self.json_file_path = json_file_path
        self.operator_segments = operator_segments
        self.caller_segments = caller_segments
        self.media_dir = media_dir
        self.root = None
        self.time_order = None
        self.time_slot_map = {}
        self.logger = setup_logging(log_level, __class__.__name__)
        self.logger.debug(
            f"Initialized EAFGenerator with {len(operator_segments)} operator segments and {len(caller_segments)} caller segments"
        )

    def generate_eaf(self) -> None:
        """
        Generate the EAF XML structure.
        """
        self.logger.debug("Starting EAF generation")
        nsmap = {
            None: "http://www.mpi.nl/tools/elan/EAFv3.0.xsd",
            "xsi": "http://www.w3.org/2001/XMLSchema-instance",
        }
        self.root = etree.Element(
            "ANNOTATION_DOCUMENT",
            attrib={
                "AUTHOR": "",
                "DATE": datetime.now().isoformat(),
                "FORMAT": "3.0",
                "VERSION": "3.0",
                "{http://www.w3.org/2001/XMLSchema-instance}noNamespaceSchemaLocation": "http://www.mpi.nl/tools/elan/EAFv3.0.xsd",
            },
            nsmap=nsmap,
        )

        # Remove the extra xmlns attribute
        etree.cleanup_namespaces(self.root)

        self._create_header()
        self._create_time_order()
        self._create_tiers()
        self._create_linguistic_types()
        self._create_constraints()

        self.logger.info("EAF structure generated successfully")

    def _create_header(self) -> None:
        """
        Create the HEADER section of the EAF file.
        """
        self.logger.debug("Creating EAF header")
        header = etree.SubElement(
            self.root, "HEADER", attrib={"MEDIA_FILE": "", "TIME_UNITS": "milliseconds"}
        )
        relative_url = self._get_relative_media_url()
        media_url = self._get_media_url()
        etree.SubElement(
            header,
            "MEDIA_DESCRIPTOR",
            attrib={
                "MIME_TYPE": "audio/x-wav",
                "MEDIA_URL": media_url,
                "RELATIVE_MEDIA_URL": relative_url,
            },
        )
        property_elem = etree.SubElement(header, "PROPERTY", attrib={"NAME": "URN"})
        property_elem.text = f"urn:nl-mpi-tools-elan-eaf:{uuid.uuid4()}"

    def _create_time_order(self) -> None:
        """
        Create the TIME_ORDER section and populate it with TIME_SLOT elements.
        """
        self.logger.debug("Creating time order")
        self.time_order = etree.SubElement(self.root, "TIME_ORDER")
        all_segments = sorted(
            self.operator_segments + self.caller_segments, key=lambda x: x["start"]
        )

        progress_bar = create_progress_bar(len(all_segments) * 2, "Creating time slots")

        for i, segment in enumerate(all_segments):
            start_slot = etree.SubElement(
                self.time_order,
                "TIME_SLOT",
                attrib={
                    "TIME_SLOT_ID": f"ts{i*2+1}",
                    "TIME_VALUE": str(int(segment["start"] * 1000)),
                },
            )
            self.time_slot_map[segment["start"]] = start_slot.attrib["TIME_SLOT_ID"]
            progress_bar.update(1)

            end_slot = etree.SubElement(
                self.time_order,
                "TIME_SLOT",
                attrib={
                    "TIME_SLOT_ID": f"ts{i*2+2}",
                    "TIME_VALUE": str(int(segment["end"] * 1000)),
                },
            )
            self.time_slot_map[segment["end"]] = end_slot.attrib["TIME_SLOT_ID"]
            progress_bar.update(1)

        progress_bar.close()

    def _create_tiers(self) -> None:
        """
        Create TIER elements for Operator and Caller, and populate them with ANNOTATION elements.
        """
        self.logger.debug("Creating tiers")
        self._create_tier("Operator", self.operator_segments)
        self._create_tier("Caller", self.caller_segments)

    def _create_tier(self, tier_id: str, segments: List[Dict[str, Any]]) -> None:
        """
        Create a TIER element and populate it with ANNOTATION elements.

        :param tier_id: ID of the tier (e.g., "Operator" or "Caller")
        :param segments: List of speech segments for this tier
        """
        tier = etree.SubElement(
            self.root,
            "TIER",
            attrib={"LINGUISTIC_TYPE_REF": "default-lt", "TIER_ID": tier_id},
        )

        progress_bar = create_progress_bar(
            len(segments), f"Creating {tier_id} annotations"
        )

        for i, segment in enumerate(segments):
            annotation = etree.SubElement(tier, "ANNOTATION")
            alignable_annotation = etree.SubElement(
                annotation,
                "ALIGNABLE_ANNOTATION",
                attrib={
                    "ANNOTATION_ID": f"{tier_id.lower()[0]}{i+1}",
                    "TIME_SLOT_REF1": self.time_slot_map[segment["start"]],
                    "TIME_SLOT_REF2": self.time_slot_map[segment["end"]],
                },
            )
            progress_bar.update(1)

        progress_bar.close()

    def _create_linguistic_types(self) -> None:
        """
        Create LINGUISTIC_TYPE elements.
        """
        self.logger.debug("Creating linguistic types")
        etree.SubElement(
            self.root,
            "LINGUISTIC_TYPE",
            attrib={
                "GRAPHIC_REFERENCES": "false",
                "LINGUISTIC_TYPE_ID": "default-lt",
                "TIME_ALIGNABLE": "true",
            },
        )

    def _create_constraints(self) -> None:
        """
        Create CONSTRAINT elements.
        """
        self.logger.debug("Creating constraints")
        constraints = [
            (
                "Time_Subdivision",
                "Time subdivision of parent annotation's time interval, no time gaps allowed within this interval",
            ),
            (
                "Symbolic_Subdivision",
                "Symbolic subdivision of a parent annotation. Annotations refering to the same parent are ordered",
            ),
            ("Symbolic_Association", "1-1 association with a parent annotation"),
            (
                "Included_In",
                "Time alignable annotations within the parent annotation's time interval, gaps are allowed",
            ),
        ]

        for stereotype, description in constraints:
            etree.SubElement(
                self.root,
                "CONSTRAINT",
                attrib={"DESCRIPTION": description, "STEREOTYPE": stereotype},
            )

    def _get_relative_media_url(self) -> str:
        """
        Generate the relative media URL based on the JSON file path and media directory.
        """
        json_path = Path(self.json_file_path)
        wav_name = f"{json_path.stem}.wav"

        if self.media_dir:
            wav_path = self.media_dir / wav_name
            rel_path = os.path.relpath(wav_path, json_path.parent)
        else:
            rel_path = wav_name

        rel_path = rel_path.replace(os.sep, "/")
        if not rel_path.startswith("."):
            rel_path = f"./{rel_path}"
        return rel_path

    def _get_media_url(self) -> str:
        """
        Generate the media URL based on the JSON file path and media directory.
        """
        json_path = Path(self.json_file_path)
        wav_name = f"{json_path.stem}.wav"

        if self.media_dir:
            wav_path = self.media_dir / wav_name
        else:
            wav_path = json_path.parent / wav_name

        if not wav_path.exists():
            return ""

        return f"file://{wav_path.absolute().as_posix()}"

    def write_to_file(self, output_path: Path) -> str:
        """
        Write the generated EAF XML to a file.

        :param output_path: Path where the EAF file should be written
        :return: Path to the generated EAF file
        :raises OSError: If there's an error creating the directory or writing the file
        """
        self.logger.debug(f"Writing EAF to file: {output_path}")
        try:
            output_path.parent.mkdir(
                parents=True, exist_ok=True
            )  # Ensure the output directory exists
            tree = etree.ElementTree(self.root)
            tree.write(
                str(output_path),
                pretty_print=True,
                xml_declaration=True,
                encoding="UTF-8",
                method="xml",
            )
            self.logger.info(f"EAF file written to {output_path}")
            return str(output_path)
        except OSError as e:
            self.logger.error(f"Error writing EAF file: {e}")
            raise
