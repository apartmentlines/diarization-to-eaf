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
   git clone https://github.com/yourusername/diarization-to-elan.git
   cd diarization-to-elan
   ```

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Usage

Run the script from the command line:

```
python src/main.py path/to/your/diarization_data.json
```

This will create an .eaf file in the same directory as the input JSON file, with the same basename.

## Configuration

You can modify the `config.ini` file to adjust logging levels and other parameters.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
