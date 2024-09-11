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
diarization-to-eaf test.json
```

This will create an .eaf file in the same directory as the input JSON file, with the same basename.

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
