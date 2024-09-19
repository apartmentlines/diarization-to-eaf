# Diarization to ELAN Converter

This Python script converts speaker diarization data from a JSON file to an ELAN Annotation Format (.eaf) file.

## Features

- Converts speaker diarization JSON data to ELAN .eaf format
- Automatically assigns speakers to 'Operator' and 'Caller' tiers
- Handles overlapping speech segments
- Provides progress reporting for long-running operations

## Requirements

- Python 3.8+
- See `requirements.txt` for Python package dependencies

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/apartmentlines/diarization-to-eaf.git
   cd diarization-to-eaf
   ```

2. Install the development package:
   ```
   pip install -e .
   ```

## Usage

Run the script from the command line:

```
diarization-to-eaf --input-file test.json --output-dir output_directory
diarization-to-eaf --input-dir input_directory --output-dir output_directory
```

Optional arguments:
- `--media-dir`: Specify the directory containing media files
- `--debug`: Enable debug logging

This will create .eaf files in the specified output directory.

## Media Directory

The `--media-dir` option allows you to specify a directory containing media files. When provided, the generated EAF files will reference media files from this directory, making it easier to manage your audio files separately from your JSON and EAF files.

## Testing

To run the tests, use the following command:

```
pytest
```

This will run all the tests in the `tests` directory.

## Development

To set up the development environment:

1. Clone the repository
2. Navigate to the project directory
3. Install the package in editable mode:

```
pip install -e .
```

This allows you to make changes to the code and immediately see the effects without reinstalling the package.

## JSON file format

The diarization segments should be a JSON array of objects with the following attributes:

```json
[
  {
    "speaker": "SPEAKER_00",
    "start": 0.005,
    "end": 3.025
  },
  {
    "speaker": "SPEAKER_01",
    "start": 4.285,
    "end": 5.285
  }
]
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
