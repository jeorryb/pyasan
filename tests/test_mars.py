"""Tests for Mars Rover Photos client."""

import pytest
from datetime import date as date_type
from unittest.mock import patch

from pyasan.mars import MarsRoverPhotosClient
from pyasan.mars_models import RoverName
from pyasan.exceptions import ValidationError


class TestMarsRoverPhotosClient:
    """Test cases for MarsRoverPhotosClient."""

    def test_init(self):
        """Test client initialization."""
        client = MarsRoverPhotosClient(api_key="test_key")
        assert client.config.api_key == "test_key"
        assert client.base_endpoint == "/mars-photos/api/v1"

    def test_validate_rover_string(self):
        """Test rover validation with string input."""
        client = MarsRoverPhotosClient(api_key="test_key")

        # Valid rover names
        assert client._validate_rover("curiosity") == "curiosity"
        assert client._validate_rover("CURIOSITY") == "curiosity"
        assert client._validate_rover("Perseverance") == "perseverance"

        # Invalid rover name
        with pytest.raises(ValidationError, match="Invalid rover"):
            client._validate_rover("invalid_rover")

    def test_validate_rover_enum(self):
        """Test rover validation with enum input."""
        client = MarsRoverPhotosClient(api_key="test_key")

        result = client._validate_rover(RoverName.CURIOSITY)
        assert result == "curiosity"

    def test_get_rover_cameras(self):
        """Test getting rover cameras."""
        client = MarsRoverPhotosClient(api_key="test_key")

        curiosity_cameras = client.get_rover_cameras("curiosity")
        assert "FHAZ" in curiosity_cameras
        assert "RHAZ" in curiosity_cameras
        assert "MAST" in curiosity_cameras

        perseverance_cameras = client.get_rover_cameras("perseverance")
        assert "NAVCAM_LEFT" in perseverance_cameras
        assert "MCZ_RIGHT" in perseverance_cameras

    def test_get_available_rovers(self):
        """Test getting available rovers."""
        client = MarsRoverPhotosClient(api_key="test_key")

        rovers = client.get_available_rovers()
        assert "curiosity" in rovers
        assert "perseverance" in rovers
        assert "opportunity" in rovers
        assert "spirit" in rovers

    def test_get_photos_validation(self):
        """Test photo retrieval parameter validation."""
        client = MarsRoverPhotosClient(api_key="test_key")

        # Must specify either sol or earth_date
        with pytest.raises(
            ValidationError, match="Must specify either sol or earth_date"
        ):
            client.get_photos("curiosity")

        # Cannot specify both sol and earth_date
        with pytest.raises(
            ValidationError, match="Cannot specify both sol and earth_date"
        ):
            client.get_photos("curiosity", sol=100, earth_date="2023-01-01")

        # Invalid sol
        with pytest.raises(ValidationError, match="Sol must be non-negative"):
            client.get_photos("curiosity", sol=-1)

        # Invalid camera for rover
        with pytest.raises(ValidationError, match="Invalid camera"):
            client.get_photos("curiosity", sol=100, camera="INVALID_CAMERA")

        # Invalid page
        with pytest.raises(ValidationError, match="Page must be positive"):
            client.get_photos("curiosity", sol=100, page=0)

    @patch("pyasan.mars.MarsRoverPhotosClient._make_request")
    def test_get_photos_by_sol_success(self, mock_request):
        """Test successful photo retrieval by sol."""
        # Mock API response
        mock_response = {
            "photos": [
                {
                    "id": 123456,
                    "sol": 1000,
                    "camera": {
                        "id": 20,
                        "name": "FHAZ",
                        "rover_id": 5,
                        "full_name": "Front Hazard Avoidance Camera",
                    },
                    "img_src": "https://example.com/image.jpg",
                    "earth_date": "2015-05-30",
                    "rover": {
                        "id": 5,
                        "name": "curiosity",
                        "landing_date": "2012-08-06",
                        "launch_date": "2011-11-26",
                        "status": "active",
                    },
                }
            ]
        }
        mock_request.return_value = mock_response

        client = MarsRoverPhotosClient(api_key="test_key")
        result = client.get_photos_by_sol("curiosity", sol=1000, camera="FHAZ")

        assert len(result.photos) == 1
        photo = result.photos[0]
        assert photo.id == 123456
        assert photo.sol == 1000
        assert photo.camera.name == "FHAZ"
        assert photo.rover.name == "curiosity"

        # Check that request was made with correct parameters
        mock_request.assert_called_once_with(
            "/mars-photos/api/v1/rovers/curiosity/photos",
            {"sol": "1000", "camera": "FHAZ"},
        )

    @patch("pyasan.mars.MarsRoverPhotosClient._make_request")
    def test_get_photos_by_earth_date_success(self, mock_request):
        """Test successful photo retrieval by Earth date."""
        mock_response = {"photos": []}
        mock_request.return_value = mock_response

        client = MarsRoverPhotosClient(api_key="test_key")
        result = client.get_photos_by_earth_date("curiosity", "2015-05-30")

        assert len(result.photos) == 0

        mock_request.assert_called_once_with(
            "/mars-photos/api/v1/rovers/curiosity/photos", {"earth_date": "2015-05-30"}
        )

    @patch("pyasan.mars.MarsRoverPhotosClient._make_request")
    def test_get_latest_photos_success(self, mock_request):
        """Test successful latest photos retrieval."""
        mock_response = {"photos": []}
        mock_request.return_value = mock_response

        client = MarsRoverPhotosClient(api_key="test_key")
        result = client.get_latest_photos("curiosity")

        assert len(result.photos) == 0

        mock_request.assert_called_once_with(
            "/mars-photos/api/v1/rovers/curiosity/latest_photos"
        )

    @patch("pyasan.mars.MarsRoverPhotosClient._make_request")
    def test_get_manifest_success(self, mock_request):
        """Test successful manifest retrieval."""
        mock_response = {
            "photo_manifest": {
                "name": "Curiosity",
                "landing_date": "2012-08-06",
                "launch_date": "2011-11-26",
                "status": "active",
                "max_sol": 4000,
                "max_date": "2023-01-01",
                "total_photos": 500000,
                "photos": [
                    {
                        "sol": 0,
                        "earth_date": "2012-08-06",
                        "total_photos": 100,
                        "cameras": ["FHAZ", "RHAZ"],
                    }
                ],
            }
        }
        mock_request.return_value = mock_response

        client = MarsRoverPhotosClient(api_key="test_key")
        result = client.get_manifest("curiosity")

        manifest = result.photo_manifest
        assert manifest.name == "Curiosity"
        assert manifest.status == "active"
        assert manifest.max_sol == 4000
        assert manifest.total_photos == 500000
        assert len(manifest.photos) == 1

        mock_request.assert_called_once_with("/mars-photos/api/v1/manifests/curiosity")

    def test_validate_and_format_date_string(self):
        """Test date validation with string input."""
        client = MarsRoverPhotosClient(api_key="test_key")

        # Valid date string
        result = client._validate_and_format_date("2023-01-01")
        assert result == "2023-01-01"

        # Invalid format
        with pytest.raises(ValidationError, match="Invalid date format"):
            client._validate_and_format_date("01-01-2023")

        # Date too early
        with pytest.raises(ValidationError, match="cannot be before"):
            client._validate_and_format_date("2000-01-01")

        # Future date
        future_date = (
            date_type.today().replace(year=date_type.today().year + 1)
        ).strftime("%Y-%m-%d")
        with pytest.raises(ValidationError, match="cannot be in the future"):
            client._validate_and_format_date(future_date)

    def test_validate_and_format_date_object(self):
        """Test date validation with date object input."""
        client = MarsRoverPhotosClient(api_key="test_key")

        # Valid date object
        test_date = date_type(2023, 1, 1)
        result = client._validate_and_format_date(test_date)
        assert result == "2023-01-01"
