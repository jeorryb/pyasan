# PyASAN 🚀

A Python wrapper and command-line interface for NASA's REST APIs, including Astronomy Picture of the Day (APOD), Mars Rover Photos, and TechTransfer APIs.

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![PyPI version](https://badge.fury.io/py/pyasan.svg)](https://badge.fury.io/py/pyasan)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/pyasan)](https://pypi.org/project/pyasan/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pyasan)](https://pypi.org/project/pyasan/)

## Features

- 🌟 **Easy-to-use Python API** for NASA's APOD, Mars Rover Photos, and TechTransfer services
- 🖥️ **Beautiful command-line interface** with rich formatting
- 🔴 **Mars Rover Photos** - Access photos from Perseverance, Curiosity, Opportunity, and Spirit
- 🔬 **TechTransfer** - Search NASA patents, software, and spinoff technologies
- 🔑 **Flexible authentication** (API key or environment variables)
- 📊 **Comprehensive data models** with validation
- 🛡️ **Robust error handling** and retry logic
- 🧪 **Well-tested** with comprehensive unit tests
- 📚 **Extensible design** for future NASA APIs

## Installation

### From PyPI (Recommended)
```bash
pip install pyasan
```

### From Source (Development)
```bash
git clone https://github.com/jeorryb/pyasan.git
cd pyasan
pip install -e .
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

#### Astronomy Picture of the Day (APOD)

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

#### Mars Rover Photos

```python
from pyasan import MarsRoverPhotosClient

# Initialize client
client = MarsRoverPhotosClient(api_key="your_api_key_here")

# Get available rovers
rovers = client.get_available_rovers()
print(rovers)  # ['perseverance', 'curiosity', 'opportunity', 'spirit']

# Get photos by Martian sol (day)
photos = client.get_photos_by_sol("curiosity", sol=1000, camera="MAST")
print(f"Found {len(photos)} photos from Sol 1000")

# Get photos by Earth date
photos = client.get_photos_by_earth_date("perseverance", "2023-01-01")
for photo in photos:
    print(f"Photo ID: {photo.id}, Camera: {photo.camera.full_name}")

# Get latest photos
latest = client.get_latest_photos("curiosity")
print(f"Latest photos: {len(latest)}")

# Get mission manifest
manifest = client.get_manifest("curiosity")
print(f"Total photos: {manifest.photo_manifest.total_photos:,}")
print(f"Mission status: {manifest.photo_manifest.status}")

# Get available cameras for a rover
cameras = client.get_rover_cameras("perseverance")
print(f"Perseverance cameras: {cameras}")
```

#### TechTransfer

```python
from pyasan import TechTransferClient

# Initialize client
client = TechTransferClient(api_key="your_api_key_here")

# Search patents
patents = client.search_patents("solar energy", limit=5)
print(f"Found {len(patents)} patents")
for patent in patents:
    print(f"- {patent.title}")
    if patent.patent_number:
        print(f"  Patent Number: {patent.patent_number}")

# Search software
software = client.search_software("machine learning", limit=3)
for item in software:
    print(f"- {item.title}")
    if item.version:
        print(f"  Version: {item.version}")

# Search spinoff technologies
spinoffs = client.search_spinoffs("medical", limit=3)
for spinoff in spinoffs:
    print(f"- {spinoff.title}")
    if spinoff.company:
        print(f"  Company: {spinoff.company}")

# Search all categories at once
all_results = client.search_all("robotics", limit=2)
for category, results in all_results.items():
    if not category.endswith("_error"):
        print(f"{category}: {len(results)} results")

# Get available categories
categories = client.get_categories()
print(f"Available categories: {categories}")
```

### Command Line Interface

The CLI provides a beautiful, user-friendly interface to NASA's APIs:

#### APOD Commands

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
```

#### Mars Rover Photos Commands

```bash
# Get photos by sol (Martian day)
pyasan mars photos --rover curiosity --sol 1000 --camera MAST

# Get photos by Earth date
pyasan mars photos --rover perseverance --earth-date 2023-01-01

# Get latest photos from a rover
pyasan mars latest --rover curiosity

# Get mission manifest
pyasan mars manifest --rover curiosity

# List available cameras for a rover
pyasan mars cameras --rover perseverance

# Get photos with pagination
pyasan mars photos --rover curiosity --sol 1000 --page 2

# Hide detailed photo information
pyasan mars photos --rover curiosity --sol 1000 --no-details
```

#### TechTransfer Commands

```bash
# Search NASA patents
pyasan techtransfer patents "solar energy" --limit 5

# Search NASA software
pyasan techtransfer software "machine learning" --limit 3

# Search NASA spinoff technologies
pyasan techtransfer spinoffs "medical devices" --limit 5

# Search across all categories
pyasan techtransfer search "robotics" --limit 3

# Search specific category only
pyasan techtransfer search "artificial intelligence" --category software

# Use pagination
pyasan techtransfer patents "space technology" --page 2 --limit 10

# Hide detailed information
pyasan techtransfer patents "propulsion" --no-details

# List available categories
pyasan techtransfer categories
```

#### Global Options

```bash
# Use specific API key for any command
pyasan apod get --api-key your_api_key_here
pyasan mars photos --rover curiosity --sol 1000 --api-key your_api_key_here
pyasan techtransfer patents "space technology" --api-key your_api_key_here

# Show version
pyasan --version
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

### MarsRoverPhotosClient

The main client for interacting with NASA's Mars Rover Photos API.

#### Methods

##### `get_photos(rover, sol=None, earth_date=None, camera=None, page=None)`

Get Mars rover photos by sol or Earth date.

**Parameters:**
- `rover` (str): Rover name (perseverance, curiosity, opportunity, spirit)
- `sol` (int, optional): Martian sol (day) - cannot be used with earth_date
- `earth_date` (str|date, optional): Earth date in YYYY-MM-DD format - cannot be used with sol
- `camera` (str, optional): Camera abbreviation (e.g., FHAZ, RHAZ, MAST, NAVCAM)
- `page` (int, optional): Page number for pagination

**Returns:** `MarsPhotosResponse`

##### `get_photos_by_sol(rover, sol, camera=None, page=None)`

Get Mars rover photos by Martian sol.

**Parameters:**
- `rover` (str): Rover name
- `sol` (int): Martian sol (day)
- `camera` (str, optional): Camera abbreviation
- `page` (int, optional): Page number for pagination

**Returns:** `MarsPhotosResponse`

##### `get_photos_by_earth_date(rover, earth_date, camera=None, page=None)`

Get Mars rover photos by Earth date.

**Parameters:**
- `rover` (str): Rover name
- `earth_date` (str|date): Earth date in YYYY-MM-DD format or date object
- `camera` (str, optional): Camera abbreviation
- `page` (int, optional): Page number for pagination

**Returns:** `MarsPhotosResponse`

##### `get_latest_photos(rover)`

Get the latest photos from a Mars rover.

**Parameters:**
- `rover` (str): Rover name

**Returns:** `MarsPhotosResponse`

##### `get_manifest(rover)`

Get mission manifest for a Mars rover.

**Parameters:**
- `rover` (str): Rover name

**Returns:** `ManifestResponse`

##### `get_rover_cameras(rover)`

Get list of available cameras for a rover.

**Parameters:**
- `rover` (str): Rover name

**Returns:** `List[str]` - List of camera abbreviations

##### `get_available_rovers()`

Get list of available rovers.

**Returns:** `List[str]` - List of rover names

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

#### MarsPhoto

Represents a single Mars rover photo.

**Attributes:**
- `id` (int): Photo ID
- `sol` (int): Martian sol (day)
- `camera` (Camera): Camera information
- `img_src` (str): Image source URL
- `earth_date` (date): Earth date when photo was taken
- `rover` (Rover): Rover information

#### MarsPhotosResponse

Represents multiple Mars rover photos.

**Attributes:**
- `photos` (List[MarsPhoto]): List of Mars photos

**Methods:**
- `__len__()`: Get the number of photos
- `__iter__()`: Iterate over photos
- `__getitem__(index)`: Get photo by index

#### MissionManifest

Represents a Mars rover mission manifest.

**Attributes:**
- `name` (str): Rover name
- `landing_date` (date): Landing date on Mars
- `launch_date` (date): Launch date from Earth
- `status` (str): Mission status
- `max_sol` (int): Maximum sol with photos
- `max_date` (date): Most recent Earth date with photos
- `total_photos` (int): Total number of photos
- `photos` (List[ManifestPhoto]): Photo information by sol

#### Camera

Represents camera information.

**Attributes:**
- `id` (int): Camera ID
- `name` (str): Camera abbreviation
- `rover_id` (int): Rover ID
- `full_name` (str): Full camera name

#### Rover

Represents rover information.

**Attributes:**
- `id` (int): Rover ID
- `name` (str): Rover name
- `landing_date` (date): Landing date on Mars
- `launch_date` (date): Launch date from Earth
- `status` (str): Mission status

### TechTransferClient

The main client for interacting with NASA's TechTransfer API.

#### Methods

##### `search_patents(query, limit=None, page=None)`

Search NASA patents by query string.

**Parameters:**
- `query` (str): Search query string
- `limit` (int, optional): Maximum number of results (1-100)
- `page` (int, optional): Page number for pagination

**Returns:** `TechTransferPatentResponse` containing patent results

##### `search_software(query, limit=None, page=None)`

Search NASA software by query string.

**Parameters:**
- `query` (str): Search query string
- `limit` (int, optional): Maximum number of results (1-100)
- `page` (int, optional): Page number for pagination

**Returns:** `TechTransferSoftwareResponse` containing software results

##### `search_spinoffs(query, limit=None, page=None)`

Search NASA spinoff technologies by query string.

**Parameters:**
- `query` (str): Search query string
- `limit` (int, optional): Maximum number of results (1-100)
- `page` (int, optional): Page number for pagination

**Returns:** `TechTransferSpinoffResponse` containing spinoff results

##### `search_all(query, category=None, limit=None, page=None)`

Search across all TechTransfer categories or a specific category.

**Parameters:**
- `query` (str): Search query string
- `category` (str, optional): Specific category ('patent', 'software', 'spinoff')
- `limit` (int, optional): Maximum number of results per category
- `page` (int, optional): Page number for pagination

**Returns:** Dictionary with category names as keys and response objects as values

##### `get_categories()`

Get list of available TechTransfer categories.

**Returns:** List of category names

#### TechTransfer Data Models

##### TechTransferPatent

Represents a NASA patent.

**Attributes:**
- `id` (str): Patent ID
- `title` (str): Patent title
- `abstract` (str): Patent abstract
- `patent_number` (str): Patent number
- `case_number` (str): NASA case number
- `publication_date` (date): Publication date
- `category` (str): Technology category
- `center` (str): NASA center
- `innovator` (str): Inventor/innovator
- `contact` (str): Contact information

##### TechTransferSoftware

Represents NASA software.

**Attributes:**
- `id` (str): Software ID
- `title` (str): Software title
- `description` (str): Software description
- `release_date` (date): Release date
- `version` (str): Software version
- `category` (str): Technology category
- `center` (str): NASA center
- `language` (str): Programming language
- `license` (str): License information
- `contact` (str): Contact information

##### TechTransferSpinoff

Represents a NASA spinoff technology.

**Attributes:**
- `id` (str): Spinoff ID
- `title` (str): Spinoff title
- `description` (str): Spinoff description
- `publication_year` (int): Publication year
- `category` (str): Technology category
- `center` (str): NASA center
- `company` (str): Company name
- `state` (str): State
- `benefits` (str): Benefits description
- `applications` (str): Applications

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
- [x] Mars Rover Photos API
- [x] TechTransfer API support
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
- [TechTransfer API Documentation](https://technology.nasa.gov/api/)
- [PyPI Package](https://pypi.org/project/pyasan/) (when published)
- [GitHub Repository](https://github.com/yourusername/pyasan)

---

Made with ❤️ for the astronomy and Python communities.
