"""NASA TechTransfer API client."""

from typing import Optional, Union, Dict, Any
from urllib.parse import quote_plus

from .client import NASAClient
from .config import Config
from .exceptions import ValidationError
from .techtransfer_models import (
    TechTransferPatentResponse,
    TechTransferSoftwareResponse, 
    TechTransferSpinoffResponse,
    TechTransferCategory,
    TechTransferPatent,
    TechTransferSoftware,
    TechTransferSpinoff
)


class TechTransferClient(NASAClient):
    """Client for NASA's TechTransfer API."""

    def __init__(self, api_key: Optional[str] = None, config: Optional[Config] = None):
        """
        Initialize TechTransfer client.

        Args:
            api_key: NASA API key
            config: Configuration object
        """
        super().__init__(api_key=api_key, config=config)
        # TechTransfer API uses a different base URL
        self.techtransfer_base_url = "https://technology.nasa.gov/api"

    def _make_techtransfer_request(self, endpoint: str) -> Dict[str, Any]:
        """
        Make a request to the TechTransfer API.

        Args:
            endpoint: API endpoint path

        Returns:
            JSON response data

        Raises:
            APIError: If the request fails
        """
        url = f"{self.techtransfer_base_url}{endpoint}"

        try:
            response = self.session.request(
                method="GET", url=url, timeout=self.config.timeout
            )

            if not response.ok:
                from .exceptions import APIError
                raise APIError(
                    f"TechTransfer API request failed with status {response.status_code}: "
                    f"{response.text}",
                    status_code=response.status_code,
                )

            return response.json()

        except Exception as e:
            from .exceptions import APIError
            if isinstance(e, APIError):
                raise
            raise APIError(f"TechTransfer request failed: {str(e)}")

    def search_patents(
        self,
        query: str,
        limit: Optional[int] = None,
        page: Optional[int] = None
    ) -> TechTransferPatentResponse:
        """
        Search NASA patents.

        Args:
            query: Search query string
            limit: Maximum number of results to return
            page: Page number for pagination

        Returns:
            TechTransferPatentResponse containing patent results

        Raises:
            ValidationError: If parameters are invalid
            APIError: If the API request fails
        """
        if not query or not query.strip():
            raise ValidationError("Query cannot be empty")

        # TechTransfer API uses URL path for query, not parameters
        query_encoded = quote_plus(query.strip())
        endpoint = f"/query/patent/{query_encoded}"
        
        try:
            response_data = self._make_techtransfer_request(endpoint)
        except Exception as e:
            # If API call fails, return empty response
            return TechTransferPatentResponse(results=[], count=0)
        
        # Handle TechTransfer API response format
        if isinstance(response_data, dict) and "results" in response_data:
            results_array = response_data["results"]
            count = response_data.get("count", len(results_array))
            
            # Parse TechTransfer API array format into patent objects
            patents = []
            for item in results_array:
                if isinstance(item, list) and len(item) >= 13:
                    try:
                        # TechTransfer API returns arrays with specific indices
                        patent = TechTransferPatent(
                            id=item[0] if len(item) > 0 else None,
                            case_number=item[1] if len(item) > 1 else None,
                            title=item[2].replace('<span class="highlight">', '').replace('</span>', '') if len(item) > 2 else "",
                            abstract=item[3].replace('<span class="highlight">', '').replace('</span>', '') if len(item) > 3 else None,
                            patent_number=item[4] if len(item) > 4 else None,
                            category=item[5] if len(item) > 5 else None,
                            center=item[9] if len(item) > 9 else None,
                            # Other fields may be available in different positions
                        )
                        patents.append(patent)
                    except Exception:
                        # Skip items that can't be parsed
                        continue
                        
            # Apply limit if specified
            if limit and len(patents) > limit:
                patents = patents[:limit]
            
            return TechTransferPatentResponse(results=patents, count=len(patents))
        else:
            return TechTransferPatentResponse(results=[], count=0)

    def search_software(
        self,
        query: str,
        limit: Optional[int] = None,
        page: Optional[int] = None
    ) -> TechTransferSoftwareResponse:
        """
        Search NASA software.

        Args:
            query: Search query string
            limit: Maximum number of results to return
            page: Page number for pagination

        Returns:
            TechTransferSoftwareResponse containing software results

        Raises:
            ValidationError: If parameters are invalid
            APIError: If the API request fails
        """
        if not query or not query.strip():
            raise ValidationError("Query cannot be empty")

        # TechTransfer API uses URL path for query, not parameters
        query_encoded = quote_plus(query.strip())
        endpoint = f"/query/software/{query_encoded}"
        
        try:
            response_data = self._make_techtransfer_request(endpoint)
        except Exception as e:
            # If API call fails, return empty response
            return TechTransferSoftwareResponse(results=[], count=0)
        
        # Handle TechTransfer API response format
        if isinstance(response_data, dict) and "results" in response_data:
            results_array = response_data["results"]
            count = response_data.get("count", len(results_array))
            
            # Parse TechTransfer API array format into software objects
            software_items = []
            for item in results_array:
                if isinstance(item, list) and len(item) >= 10:
                    try:
                        # TechTransfer API returns arrays with specific indices for software
                        software = TechTransferSoftware(
                            id=item[0] if len(item) > 0 else None,
                            case_number=item[1] if len(item) > 1 else None,
                            title=item[2].replace('<span class="highlight">', '').replace('</span>', '') if len(item) > 2 else "",
                            description=item[3].replace('<span class="highlight">', '').replace('</span>', '') if len(item) > 3 else None,
                            version=item[4] if len(item) > 4 else None,
                            category=item[5] if len(item) > 5 else None,
                            license=item[6] if len(item) > 6 else None,
                            # item[7] appears to be empty or additional info
                            # item[8] appears to be a URL or link
                            center=item[9] if len(item) > 9 else None,
                        )
                        software_items.append(software)
                    except Exception:
                        # Skip items that can't be parsed
                        continue
                        
            # Apply limit if specified
            if limit and len(software_items) > limit:
                software_items = software_items[:limit]
            
            return TechTransferSoftwareResponse(results=software_items, count=len(software_items))
        else:
            return TechTransferSoftwareResponse(results=[], count=0)

    def search_spinoffs(
        self,
        query: str,
        limit: Optional[int] = None,
        page: Optional[int] = None
    ) -> TechTransferSpinoffResponse:
        """
        Search NASA spinoff technologies.

        Args:
            query: Search query string
            limit: Maximum number of results to return
            page: Page number for pagination

        Returns:
            TechTransferSpinoffResponse containing spinoff results

        Raises:
            ValidationError: If parameters are invalid
            APIError: If the API request fails
        """
        if not query or not query.strip():
            raise ValidationError("Query cannot be empty")

        # TechTransfer API uses URL path for query, not parameters
        query_encoded = quote_plus(query.strip())
        endpoint = f"/query/spinoff/{query_encoded}"
        
        try:
            response_data = self._make_techtransfer_request(endpoint)
        except Exception as e:
            # If API call fails, return empty response
            return TechTransferSpinoffResponse(results=[], count=0)
        
        # Handle TechTransfer API response format
        if isinstance(response_data, dict) and "results" in response_data:
            results_array = response_data["results"]
            count = response_data.get("count", len(results_array))
            
            # Parse TechTransfer API array format into spinoff objects
            spinoffs = []
            for item in results_array:
                if isinstance(item, list) and len(item) >= 10:
                    try:
                        # TechTransfer API returns arrays with specific indices for spinoffs
                        spinoff = TechTransferSpinoff(
                            id=item[0] if len(item) > 0 else None,
                            case_number=item[1] if len(item) > 1 else None,
                            title=item[2].replace('<span class="highlight">', '').replace('</span>', '') if len(item) > 2 else "",
                            description=item[3].replace('<span class="highlight">', '').replace('</span>', '') if len(item) > 3 else None,
                            # item[4] appears to be another ID or empty
                            category=item[5] if len(item) > 5 else None,
                            # item[6-8] appear to be empty or additional fields
                            center=item[9] if len(item) > 9 else None,
                            # Try to extract publication year from the description or other fields
                            publication_year=None,  # Could be parsed from description if available
                        )
                        spinoffs.append(spinoff)
                    except Exception:
                        # Skip items that can't be parsed
                        continue
                        
            # Apply limit if specified
            if limit and len(spinoffs) > limit:
                spinoffs = spinoffs[:limit]
            
            return TechTransferSpinoffResponse(results=spinoffs, count=len(spinoffs))
        else:
            return TechTransferSpinoffResponse(results=[], count=0)

    def search_all(
        self,
        query: str,
        category: Optional[Union[str, TechTransferCategory]] = None,
        limit: Optional[int] = None,
        page: Optional[int] = None
    ) -> Dict[str, Union[TechTransferPatentResponse, TechTransferSoftwareResponse, TechTransferSpinoffResponse]]:
        """
        Search across all TechTransfer categories or a specific category.

        Args:
            query: Search query string
            category: Specific category to search (patent, software, spinoff). If None, searches all.
            limit: Maximum number of results per category
            page: Page number for pagination

        Returns:
            Dictionary with category names as keys and response objects as values

        Raises:
            ValidationError: If parameters are invalid
            APIError: If the API request fails
        """
        if not query or not query.strip():
            raise ValidationError("Query cannot be empty")

        results = {}
        
        # Determine which categories to search
        if category is not None:
            if isinstance(category, str):
                try:
                    category = TechTransferCategory(category.lower())
                except ValueError:
                    valid_categories = [c.value for c in TechTransferCategory]
                    raise ValidationError(
                        f"Invalid category '{category}'. Valid categories: {', '.join(valid_categories)}"
                    )
            categories = [category]
        else:
            categories = list(TechTransferCategory)

        # Search each category
        for cat in categories:
            try:
                if cat == TechTransferCategory.PATENT:
                    results["patents"] = self.search_patents(query, limit, page)
                elif cat == TechTransferCategory.SOFTWARE:
                    results["software"] = self.search_software(query, limit, page)
                elif cat == TechTransferCategory.SPINOFF:
                    results["spinoffs"] = self.search_spinoffs(query, limit, page)
            except Exception as e:
                # Continue with other categories if one fails
                results[f"{cat.value}_error"] = str(e)

        return results

    def get_categories(self) -> list[str]:
        """
        Get list of available TechTransfer categories.

        Returns:
            List of category names
        """
        return [category.value for category in TechTransferCategory]
