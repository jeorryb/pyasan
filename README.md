# PyASAN 🚀

A Python wrapper and command-line interface for NASA's REST APIs, starting with the Astronomy Picture of the Day (APOD) API.

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## Features

- 🌟 **Easy-to-use Python API** for NASA's APOD service
- 🖥️ **Beautiful command-line interface** with rich formatting
- 🔑 **Flexible authentication** (API key or environment variables)
- 📊 **Comprehensive data models** with validation
- 🛡️ **Robust error handling** and retry logic
- 🧪 **Well-tested** with comprehensive unit tests
- 📚 **Extensible design** for future NASA APIs

## Installation

### From PyPI (when published)
```bash
pip install pyasan
```

### From Source
```bash
git clone https://github.com/yourusername/pyasan.git
cd pyasan
pip install -e .
```

### Development Installation
```bash
git clone https://github.com/yourusername/pyasan.git
cd pyasan
pip install -e ".[dev]"
```

## Quick Start

### Get Your NASA API Key

1. Visit [https://api.nasa.gov/](https://api.nasa.gov/)
2. Fill out the form to get your free API key
3. Set it as an environment variable:
   ```bash
   export NASA_API_KEY=your_api_key_here
   ```

### Python API

```python
from pyasan import APODClient

# Initialize client (uses NASA_API_KEY env var by default)
client = APODClient()

# Or provide API key directly
client = APODClient(api_key="your_api_key_here")

# Get today's APOD
apod = client.get_apod()
print(f"Title: {apod.title}")
print(f"Date: {apod.date}")
print(f"URL: {apod.url}")
print(f"Explanation: {apod.explanation}")

# Get APOD for a specific date
apod = client.get_apod(date="2023-01-01", hd=True)

# Get random APOD
random_apod = client.get_random_apod()

# Get multiple random APODs
random_apods = client.get_random_apod(count=5)
for apod in random_apods:
    print(apod.title)

# Get APOD for a date range
apods = client.get_apod_range(
    start_date="2023-01-01", 
    end_date="2023-01-07"
)

# Get recent APODs
recent = client.get_recent_apods(days=7)
```

### Command Line Interface

The CLI provides a beautiful, user-friendly interface to NASA's APOD API:

```bash
# Get today's APOD
pyasan apod get

# Get APOD for a specific date
pyasan apod get --date 2023-01-01

# Get HD version
pyasan apod get --date 2023-01-01 --hd

# Get random APOD
pyasan apod random

# Get 5 random APODs
pyasan apod random --count 5

# Get APODs for a date range
pyasan apod range --start-date 2023-01-01 --end-date 2023-01-07

# Get recent APODs
pyasan apod recent --days 7

# Hide explanation text for cleaner output
pyasan apod get --no-explanation

# Use specific API key
pyasan apod get --api-key your_api_key_here
```

## API Reference

### APODClient

The main client for interacting with NASA's APOD API.

#### Methods

##### `get_apod(date=None, hd=False, thumbs=False)`

Get Astronomy Picture of the Day for a specific date.

**Parameters:**
- `date` (str|date, optional): Date in YYYY-MM-DD format or date object. Defaults to today.
- `hd` (bool): Return HD image URL if available
- `thumbs` (bool): Return thumbnail URL for videos

**Returns:** `APODResponse`

##### `get_random_apod(count=1, hd=False, thumbs=False)`

Get random Astronomy Picture(s) of the Day.

**Parameters:**
- `count` (int): Number of random images to retrieve (1-100)
- `hd` (bool): Return HD image URLs if available  
- `thumbs` (bool): Return thumbnail URLs for videos

**Returns:** `APODResponse` if count=1, `APODBatch` if count>1

##### `get_apod_range(start_date, end_date, hd=False, thumbs=False)`

Get Astronomy Pictures of the Day for a date range.

**Parameters:**
- `start_date` (str|date): Start date in YYYY-MM-DD format or date object
- `end_date` (str|date): End date in YYYY-MM-DD format or date object  
- `hd` (bool): Return HD image URLs if available
- `thumbs` (bool): Return thumbnail URLs for videos

**Returns:** `APODBatch`

##### `get_recent_apods(days=7, hd=False, thumbs=False)`

Get recent Astronomy Pictures of the Day.

**Parameters:**
- `days` (int): Number of recent days to retrieve (1-100)
- `hd` (bool): Return HD image URLs if available
- `thumbs` (bool): Return thumbnail URLs for videos

**Returns:** `APODBatch`

### Data Models

#### APODResponse

Represents a single APOD entry.

**Attributes:**
- `title` (str): The title of the image
- `date` (date): The date of the image  
- `explanation` (str): The explanation of the image
- `url` (str): The URL of the image
- `media_type` (str): The type of media (image or video)
- `hdurl` (str, optional): The URL of the HD image
- `thumbnail_url` (str, optional): The URL of the thumbnail
- `copyright` (str, optional): The copyright information

**Properties:**
- `is_video` (bool): Check if the media is a video
- `is_image` (bool): Check if the media is an image

#### APODBatch

Represents multiple APOD entries.

**Attributes:**
- `items` (List[APODResponse]): List of APOD responses

**Methods:**
- `__len__()`: Get the number of items
- `__iter__()`: Iterate over items  
- `__getitem__(index)`: Get item by index

## Configuration

### Environment Variables

- `NASA_API_KEY`: Your NASA API key
- `NASA_API_TOKEN`: Alternative name for the API key

### API Key Sources (in order of precedence)

1. Direct parameter: `APODClient(api_key="your_key")`
2. Environment variable: `NASA_API_KEY`
3. Environment variable: `NASA_API_TOKEN`  
4. Default: `DEMO_KEY` (limited requests)

## Error Handling

PyASAN provides comprehensive error handling:

```python
from pyasan import APODClient
from pyasan.exceptions import (
    ValidationError, 
    APIError, 
    AuthenticationError, 
    RateLimitError
)

client = APODClient()

try:
    apod = client.get_apod(date="invalid-date")
except ValidationError as e:
    print(f"Invalid input: {e}")
except AuthenticationError as e:
    print(f"API key issue: {e}")
except RateLimitError as e:
    print(f"Rate limit exceeded: {e}")
except APIError as e:
    print(f"API error: {e}")
```

## Development

### Setup Development Environment

```bash
git clone https://github.com/yourusername/pyasan.git
cd pyasan
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=pyasan

# Run specific test file
pytest tests/test_apod.py
```

### Code Formatting

```bash
# Format code with black
black pyasan tests

# Check with flake8
flake8 pyasan tests

# Type checking with mypy
mypy pyasan
```

## Roadmap

- [x] APOD API support
- [ ] Mars Rover Photos API
- [ ] Earth Polychromatic Imaging Camera (EPIC) API  
- [ ] Near Earth Object Web Service (NeoWs)
- [ ] Exoplanet Archive API
- [ ] Image and Video Library API
- [ ] Async support
- [ ] Caching support
- [ ] Image download utilities

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- NASA for providing free access to their amazing APIs
- The astronomy community for inspiring space exploration
- All contributors who help improve this project

## Links

- [NASA API Portal](https://api.nasa.gov/)
- [APOD API Documentation](https://api.nasa.gov/planetary/apod)
- [PyPI Package](https://pypi.org/project/pyasan/) (when published)
- [GitHub Repository](https://github.com/yourusername/pyasan)

---

Made with ❤️ for the astronomy and Python communities.
