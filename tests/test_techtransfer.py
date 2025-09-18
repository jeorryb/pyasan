"""Tests for TechTransfer client."""

import pytest
from unittest.mock import patch, Mock
from datetime import date as date_type

from pyasan.techtransfer import TechTransferClient
from pyasan.techtransfer_models import (
    TechTransferPatent,
    TechTransferSoftware,
    TechTransferSpinoff,
    TechTransferPatentResponse,
    TechTransferSoftwareResponse,
    TechTransferSpinoffResponse,
    TechTransferCategory,
)
from pyasan.exceptions import ValidationError, APIError


class TestTechTransferClient:
    """Test cases for TechTransferClient."""

    def test_init(self):
        """Test client initialization."""
        client = TechTransferClient(api_key="test_key")
        assert client.config.api_key == "test_key"
        assert client.techtransfer_base_url == "https://technology.nasa.gov/api"

    def test_init_without_api_key(self):
        """Test client initialization without API key."""
        client = TechTransferClient()
        assert client.config.api_key == "DEMO_KEY"

    @patch("pyasan.techtransfer.TechTransferClient._make_techtransfer_request")
    def test_search_patents_success(self, mock_request):
        """Test successful patent search."""
        # Mock API response
        mock_response = {
            "results": [
                [
                    "1",
                    "LAR-TOPS-123",
                    "Test Patent Title",
                    "Test patent abstract",
                    "US123456",
                    "optics",
                    None,
                    None,
                    None,
                    "LARC",
                    None,
                    None,
                    None,
                ]
            ]
        }
        mock_request.return_value = mock_response

        client = TechTransferClient(api_key="test_key")
        result = client.search_patents("laser", limit=5)

        assert isinstance(result, TechTransferPatentResponse)
        assert len(result.results) == 1
        assert result.results[0].title == "Test Patent Title"
        assert result.results[0].patent_number == "US123456"
        assert result.results[0].category == "optics"
        assert result.results[0].center == "LARC"

        mock_request.assert_called_once_with("/query/patent/laser")

    @patch("pyasan.techtransfer.TechTransferClient._make_techtransfer_request")
    def test_search_patents_empty_response(self, mock_request):
        """Test patent search with empty response."""
        mock_request.return_value = {"results": []}

        client = TechTransferClient(api_key="test_key")
        result = client.search_patents("nonexistent")

        assert isinstance(result, TechTransferPatentResponse)
        assert len(result.results) == 0

    @patch("pyasan.techtransfer.TechTransferClient._make_techtransfer_request")
    def test_search_patents_api_error(self, mock_request):
        """Test patent search with API error."""
        mock_request.side_effect = APIError("API Error")

        client = TechTransferClient(api_key="test_key")
        result = client.search_patents("test")

        assert isinstance(result, TechTransferPatentResponse)
        assert len(result.results) == 0

    def test_search_patents_validation_error(self):
        """Test patent search with invalid query."""
        client = TechTransferClient(api_key="test_key")

        with pytest.raises(ValidationError, match="Query cannot be empty"):
            client.search_patents("")

        with pytest.raises(ValidationError, match="Query cannot be empty"):
            client.search_patents("   ")

    @patch("pyasan.techtransfer.TechTransferClient._make_techtransfer_request")
    def test_search_software_success(self, mock_request):
        """Test successful software search."""
        # Mock API response
        mock_response = {
            "results": [
                [
                    "1",
                    "LEW-19323-1",
                    "Test Software Title",
                    "Test software description",
                    "1.0",
                    "data processing",
                    "Open Source",
                    None,
                    None,
                    "GRC",
                ]
            ]
        }
        mock_request.return_value = mock_response

        client = TechTransferClient(api_key="test_key")
        result = client.search_software("python", limit=3)

        assert isinstance(result, TechTransferSoftwareResponse)
        assert len(result.results) == 1
        assert result.results[0].title == "Test Software Title"
        assert result.results[0].version == "1.0"
        assert result.results[0].category == "data processing"
        assert result.results[0].license == "Open Source"
        assert result.results[0].center == "GRC"

        mock_request.assert_called_once_with("/query/software/python")

    @patch("pyasan.techtransfer.TechTransferClient._make_techtransfer_request")
    def test_search_spinoffs_success(self, mock_request):
        """Test successful spinoff search."""
        # Mock API response
        mock_response = {
            "results": [
                [
                    "1",
                    "SPINOFF-123",
                    "Test Spinoff Title",
                    "Test spinoff description",
                    None,
                    "medical",
                    None,
                    None,
                    None,
                    "JSC",
                ]
            ]
        }
        mock_request.return_value = mock_response

        client = TechTransferClient(api_key="test_key")
        result = client.search_spinoffs("medical", limit=2)

        assert isinstance(result, TechTransferSpinoffResponse)
        assert len(result.results) == 1
        assert result.results[0].title == "Test Spinoff Title"
        assert result.results[0].category == "medical"
        assert result.results[0].center == "JSC"

        mock_request.assert_called_once_with("/query/spinoff/medical")

    @patch("pyasan.techtransfer.TechTransferClient.search_patents")
    @patch("pyasan.techtransfer.TechTransferClient.search_software")
    @patch("pyasan.techtransfer.TechTransferClient.search_spinoffs")
    def test_search_all_success(self, mock_spinoffs, mock_software, mock_patents):
        """Test successful search across all categories."""
        # Mock responses
        mock_patents.return_value = TechTransferPatentResponse(results=[], count=0)
        mock_software.return_value = TechTransferSoftwareResponse(results=[], count=0)
        mock_spinoffs.return_value = TechTransferSpinoffResponse(results=[], count=0)

        client = TechTransferClient(api_key="test_key")
        result = client.search_all("test", limit=5)

        assert "patents" in result
        assert "software" in result
        assert "spinoffs" in result
        assert len(result) == 3

        mock_patents.assert_called_once_with("test", 5, None)
        mock_software.assert_called_once_with("test", 5, None)
        mock_spinoffs.assert_called_once_with("test", 5, None)

    @patch("pyasan.techtransfer.TechTransferClient.search_patents")
    def test_search_all_specific_category(self, mock_patents):
        """Test search with specific category."""
        mock_patents.return_value = TechTransferPatentResponse(results=[], count=0)

        client = TechTransferClient(api_key="test_key")
        result = client.search_all("test", category="patent", limit=5)

        assert "patents" in result
        assert len(result) == 1

        mock_patents.assert_called_once_with("test", 5, None)

    def test_search_all_invalid_category(self):
        """Test search with invalid category."""
        client = TechTransferClient(api_key="test_key")

        with pytest.raises(ValidationError, match="Invalid category"):
            client.search_all("test", category="invalid")

    @patch("pyasan.techtransfer.TechTransferClient.search_patents")
    def test_search_all_with_error(self, mock_patents):
        """Test search_all with API error in one category."""
        mock_patents.side_effect = APIError("Test error")

        client = TechTransferClient(api_key="test_key")
        result = client.search_all("test", category="patent")

        assert "patent_error" in result
        assert result["patent_error"] == "Test error"

    def test_get_categories(self):
        """Test getting available categories."""
        client = TechTransferClient(api_key="test_key")
        categories = client.get_categories()

        assert "patent" in categories
        assert "software" in categories
        assert "spinoff" in categories
        assert len(categories) == 3

    @patch("requests.Session.request")
    def test_make_techtransfer_request_success(self, mock_request):
        """Test successful TechTransfer API request."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {"results": []}
        mock_request.return_value = mock_response

        client = TechTransferClient(api_key="test_key")
        result = client._make_techtransfer_request("/test/endpoint")

        assert result == {"results": []}
        mock_request.assert_called_once()

    @patch("requests.Session.request")
    def test_make_techtransfer_request_http_error(self, mock_request):
        """Test TechTransfer API request with HTTP error."""
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_request.return_value = mock_response

        client = TechTransferClient(api_key="test_key")

        with pytest.raises(APIError, match="TechTransfer API request failed"):
            client._make_techtransfer_request("/test/endpoint")

    @patch("requests.Session.request")
    def test_make_techtransfer_request_connection_error(self, mock_request):
        """Test TechTransfer API request with connection error."""
        mock_request.side_effect = Exception("Connection error")

        client = TechTransferClient(api_key="test_key")

        with pytest.raises(APIError, match="TechTransfer request failed"):
            client._make_techtransfer_request("/test/endpoint")


class TestTechTransferModels:
    """Test cases for TechTransfer models."""

    def test_techtransfer_patent_creation(self):
        """Test TechTransferPatent model creation."""
        patent = TechTransferPatent(
            id="1",
            title="Test Patent",
            abstract="Test abstract",
            patent_number="US123456",
            case_number="LAR-TOPS-123",
            category="optics",
            center="LARC",
            publication_date=None,
            innovator=None,
            contact=None,
        )

        assert patent.title == "Test Patent"
        assert patent.patent_number == "US123456"
        assert patent.category == "optics"

    def test_techtransfer_software_creation(self):
        """Test TechTransferSoftware model creation."""
        software = TechTransferSoftware(
            id="1",
            title="Test Software",
            description="Test description",
            version="1.0",
            category="data processing",
            license="Open Source",
            center="GRC",
            release_date=None,
            language=None,
            contact=None,
        )

        assert software.title == "Test Software"
        assert software.version == "1.0"
        assert software.license == "Open Source"

    def test_techtransfer_spinoff_creation(self):
        """Test TechTransferSpinoff model creation."""
        spinoff = TechTransferSpinoff(
            id="1",
            title="Test Spinoff",
            description="Test description",
            publication_year=2023,
            category="medical",
            center="JSC",
            company=None,
            state=None,
            benefits=None,
            applications=None,
        )

        assert spinoff.title == "Test Spinoff"
        assert spinoff.publication_year == 2023
        assert spinoff.category == "medical"

    def test_techtransfer_category_enum(self):
        """Test TechTransferCategory enum."""
        assert TechTransferCategory.PATENT == "patent"
        assert TechTransferCategory.SOFTWARE == "software"
        assert TechTransferCategory.SPINOFF == "spinoff"

    def test_techtransfer_patent_response(self):
        """Test TechTransferPatentResponse model."""
        patent = TechTransferPatent(
            title="Test Patent",
            publication_date=None,
            innovator=None,
            contact=None,
        )
        response = TechTransferPatentResponse(results=[patent], count=1)

        assert len(response) == 1
        assert response.count == 1
        assert response[0] == patent
        assert list(response) == [patent]

    def test_techtransfer_software_response(self):
        """Test TechTransferSoftwareResponse model."""
        software = TechTransferSoftware(
            title="Test Software",
            release_date=None,
            language=None,
            contact=None,
        )
        response = TechTransferSoftwareResponse(results=[software], count=1)

        assert len(response) == 1
        assert response.count == 1
        assert response[0] == software

    def test_techtransfer_spinoff_response(self):
        """Test TechTransferSpinoffResponse model."""
        spinoff = TechTransferSpinoff(
            title="Test Spinoff",
            company=None,
            state=None,
            benefits=None,
            applications=None,
        )
        response = TechTransferSpinoffResponse(results=[spinoff], count=1)

        assert len(response) == 1
        assert response.count == 1
        assert response[0] == spinoff

    def test_date_validation(self):
        """Test date field validation in models."""
        # Test with valid date
        patent = TechTransferPatent(
            title="Test Patent",
            publication_date=date_type(2023, 1, 1),
            innovator=None,
            contact=None,
        )
        assert patent.publication_date == date_type(2023, 1, 1)

        # Test with None
        patent = TechTransferPatent(
            title="Test Patent",
            publication_date=None,
            innovator=None,
            contact=None,
        )
        assert patent.publication_date is None

    def test_year_validation(self):
        """Test year field validation in models."""
        # Test with valid year
        spinoff = TechTransferSpinoff(
            title="Test Spinoff",
            publication_year=2023,
            company=None,
            state=None,
            benefits=None,
            applications=None,
        )
        assert spinoff.publication_year == 2023

        # Test with None
        spinoff = TechTransferSpinoff(
            title="Test Spinoff",
            publication_year=None,
            company=None,
            state=None,
            benefits=None,
            applications=None,
        )
        assert spinoff.publication_year is None
