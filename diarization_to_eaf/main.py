#!/usr/bin/env python3

import argparse
import sys
from typing import Optional
from pathlib import Path

from diarization_to_eaf.diarization_processor import DiarizationProcessor
from diarization_to_eaf.eaf_generator import EAFGenerator
from diarization_to_eaf.utils import setup_logging, check_file_exists


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.

    :return: Parsed arguments
    :rtype: argparse.Namespace
    """
    parser = argparse.ArgumentParser(
        description="Convert speaker diarization JSON to ELAN Annotation Format (EAF)"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--input-file",
        type=str,
        help="Path to the input JSON file containing speaker diarization data",
    )
    group.add_argument(
        "--input-dir",
        type=str,
        help="Path to the input directory containing JSON files",
    )
    parser.add_argument(
        "--output-dir", type=str, help="Path to the output directory for EAF files"
    )
    parser.add_argument(
        "--media-dir", type=str, help="Path to the directory containing media files"
    )
    parser.add_argument(
        "--force", action="store_true", help="Overwrite existing output files"
    )
    parser.add_argument(
        "-d", "--debug", action="store_true", help="Enable debug logging"
    )
    return parser.parse_args()


def process_file(
    input_path: Path, output_path: Path, media_dir: Optional[Path], log_level: str, force: bool
) -> None:
    """
    Process a single JSON file and generate an EAF file.

    :param input_path: Path to the input JSON file
    :param output_path: Path to the output EAF file
    :param media_dir: Optional path to the directory containing media files
    :param log_level: Logging level
    :param force: Whether to overwrite existing output files
    """
    logger = setup_logging(log_level, "process_file")

    try:
        if output_path.exists() and not force:
            logger.info(f"Output file already exists: {output_path}. Skipping. Use --force to overwrite.")
            return

        # Process diarization data
        logger.debug(f"Processing input file: {input_path}")
        processor = DiarizationProcessor(str(input_path), log_level)
        processor.load_and_validate_data()
        operator_segments, caller_segments = processor.process_diarization_data()

        # Generate EAF file
        logger.debug("Initializing EAFGenerator")
        generator = EAFGenerator(
            str(input_path), operator_segments, caller_segments, media_dir, log_level
        )
        generator.generate_eaf()
        eaf_file_path = generator.write_to_file(output_path)

        logger.info(f"EAF file successfully generated: {eaf_file_path}")

    except Exception as e:
        logger.exception(f"An error occurred while processing {input_path}: {e}")


def main() -> None:
    """
    Main execution flow of the script.
    """
    args = parse_arguments()

    # Setup logging
    log_level = "DEBUG" if args.debug else "INFO"
    logger = setup_logging(log_level, "main")

    try:
        media_dir = Path(args.media_dir) if args.media_dir else None

        if args.input_file:
            # Process single file
            if not check_file_exists(args.input_file):
                raise FileNotFoundError(f"Input file not found: {args.input_file}")

            input_path = Path(args.input_file)
            output_dir = Path(args.output_dir) if args.output_dir else input_path.parent
            output_path = output_dir / input_path.with_suffix(".eaf").name

            process_file(input_path, output_path, media_dir, log_level, args.force)

        elif args.input_dir:
            # Process all JSON files in the input directory
            input_dir = Path(args.input_dir)
            if not input_dir.is_dir():
                raise NotADirectoryError(f"Input directory not found: {args.input_dir}")

            output_dir = Path(args.output_dir) if args.output_dir else input_dir

            for json_file in input_dir.glob("*.json"):
                output_path = output_dir / json_file.with_suffix(".eaf").name
                process_file(json_file, output_path, media_dir, log_level, args.force)

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except NotADirectoryError as e:
        logger.error(f"Directory not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
