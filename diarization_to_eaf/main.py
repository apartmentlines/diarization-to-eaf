import argparse
import sys
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
    parser = argparse.ArgumentParser(description="Convert speaker diarization JSON to ELAN Annotation Format (EAF)")
    parser.add_argument("input_file", type=str, help="Path to the input JSON file containing speaker diarization data")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    return parser.parse_args()


def main() -> None:
    """
    Main execution flow of the script.
    """
    args = parse_arguments()

    # Setup logging
    log_level = "DEBUG" if args.verbose else "INFO"
    logger = setup_logging(log_level, "main")

    try:
        # Validate input file
        if not check_file_exists(args.input_file):
            raise FileNotFoundError(f"Input file not found: {args.input_file}")

        input_path = Path(args.input_file)
        output_path = input_path.with_suffix('.eaf')

        logger.debug(f"Processing input file: {input_path}")
        logger.debug(f"Output will be saved to: {output_path}")

        # Process diarization data
        logger.debug("Initializing DiarizationProcessor")
        processor = DiarizationProcessor(str(input_path), log_level)
        processor.load_and_validate_data()
        operator_segments, caller_segments = processor.process_diarization_data()

        # Generate EAF file
        logger.debug("Initializing EAFGenerator")
        generator = EAFGenerator(str(input_path), operator_segments, caller_segments, log_level)
        generator.generate_eaf()
        eaf_file_path = generator.write_to_file()

        logger.info(f"EAF file successfully generated: {eaf_file_path}")

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Invalid data: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
