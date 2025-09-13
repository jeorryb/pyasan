"""Tests for APOD client."""

import pytest
from datetime import date, datetime
from unittest.mock import Mock, patch

from pyasan.apod import APODClient
from pyasan.exceptions import ValidationError, APIError
from pyasan.models import APODResponse


class TestAPODClient:
    """Test cases for APODClient."""
    
    def test_init(self):
        """Test client initialization."""
        client = APODClient(api_key="test_key")
        assert client.config.api_key == "test_key"
        assert client.endpoint == "/planetary/apod"
    
    def test_validate_and_format_date_string(self):
        """Test date validation with string input."""
        client = APODClient(api_key="test_key")
        
        # Valid date string
        result = client._validate_and_format_date("2023-01-01")
        assert result == "2023-01-01"
        
        # Invalid format
        with pytest.raises(ValidationError, match="Invalid date format"):
            client._validate_and_format_date("01-01-2023")
        
        # Date before APOD start
        with pytest.raises(ValidationError, match="cannot be before"):
            client._validate_and_format_date("1995-01-01")
        
        # Future date
        future_date = (date.today().replace(year=date.today().year + 1)).strftime("%Y-%m-%d")
        with pytest.raises(ValidationError, match="cannot be in the future"):
            client._validate_and_format_date(future_date)
    
    def test_validate_and_format_date_object(self):
        """Test date validation with date object input."""
        client = APODClient(api_key="test_key")
        
        # Valid date object
        test_date = date(2023, 1, 1)
        result = client._validate_and_format_date(test_date)
        assert result == "2023-01-01"
    
    @patch('pyasan.apod.APODClient._make_request')
    def test_get_apod_success(self, mock_request):
        """Test successful APOD retrieval."""
        # Mock API response
        mock_response = {
            "title": "Test APOD",
            "date": "2023-01-01",
            "explanation": "Test explanation",
            "url": "https://example.com/image.jpg",
            "media_type": "image",
            "service_version": "v1"
        }
        mock_request.return_value = mock_response
        
        client = APODClient(api_key="test_key")
        result = client.get_apod(date="2023-01-01")
        
        assert isinstance(result, APODResponse)
        assert result.title == "Test APOD"
        assert result.date == date(2023, 1, 1)
        assert result.url == "https://example.com/image.jpg"
        
        # Check that request was made with correct parameters
        mock_request.assert_called_once_with(
            "/planetary/apod",
            {"date": "2023-01-01"}
        )
    
    @patch('pyasan.apod.APODClient._make_request')
    def test_get_apod_with_hd_and_thumbs(self, mock_request):
        """Test APOD retrieval with HD and thumbs options."""
        mock_response = {
            "title": "Test APOD",
            "date": "2023-01-01",
            "explanation": "Test explanation",
            "url": "https://example.com/image.jpg",
            "media_type": "image",
            "hdurl": "https://example.com/hd_image.jpg",
            "thumbnail_url": "https://example.com/thumb.jpg"
        }
        mock_request.return_value = mock_response
        
        client = APODClient(api_key="test_key")
        result = client.get_apod(date="2023-01-01", hd=True, thumbs=True)
        
        assert result.hdurl == "https://example.com/hd_image.jpg"
        assert result.thumbnail_url == "https://example.com/thumb.jpg"
        
        # Check that request was made with correct parameters
        mock_request.assert_called_once_with(
            "/planetary/apod",
            {"date": "2023-01-01", "hd": "true", "thumbs": "true"}
        )
    
    @patch('pyasan.apod.APODClient._make_request')
    def test_get_random_apod_single(self, mock_request):
        """Test random APOD retrieval (single)."""
        mock_response = {
            "title": "Random APOD",
            "date": "2022-05-15",
            "explanation": "Random explanation",
            "url": "https://example.com/random.jpg",
            "media_type": "image"
        }
        mock_request.return_value = mock_response
        
        client = APODClient(api_key="test_key")
        result = client.get_random_apod(count=1)
        
        assert isinstance(result, APODResponse)
        assert result.title == "Random APOD"
        
        mock_request.assert_called_once_with(
            "/planetary/apod",
            {"count": "1"}
        )
    
    def test_get_random_apod_invalid_count(self):
        """Test random APOD with invalid count."""
        client = APODClient(api_key="test_key")
        
        with pytest.raises(ValidationError, match="Count must be between 1 and 100"):
            client.get_random_apod(count=0)
        
        with pytest.raises(ValidationError, match="Count must be between 1 and 100"):
            client.get_random_apod(count=101)
    
    def test_get_apod_range_validation(self):
        """Test APOD range validation."""
        client = APODClient(api_key="test_key")
        
        # Start date after end date
        with pytest.raises(ValidationError, match="start_date must be before"):
            client.get_apod_range("2023-01-15", "2023-01-01")
        
        # Range too large
        with pytest.raises(ValidationError, match="cannot exceed 100 days"):
            client.get_apod_range("2023-01-01", "2023-05-01")
    
    def test_get_recent_apods_validation(self):
        """Test recent APODs validation."""
        client = APODClient(api_key="test_key")
        
        with pytest.raises(ValidationError, match="Days must be between 1 and 100"):
            client.get_recent_apods(days=0)
        
        with pytest.raises(ValidationError, match="Days must be between 1 and 100"):
            client.get_recent_apods(days=101)
