"""Base NASA API client."""

import time
from typing import Dict, Any, Optional
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from .config import Config
from .exceptions import APIError, AuthenticationError, RateLimitError


class NASAClient:
    """Base client for NASA APIs."""
    
    def __init__(self, api_key: Optional[str] = None, config: Optional[Config] = None):
        """
        Initialize NASA API client.
        
        Args:
            api_key: NASA API key. If not provided, will use config or environment.
            config: Configuration object. If not provided, will create default.
        """
        self.config = config or Config(api_key=api_key)
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """Create a requests session with retry strategy."""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=self.config.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _make_request(
        self, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None,
        method: str = "GET"
    ) -> Dict[str, Any]:
        """
        Make a request to the NASA API.
        
        Args:
            endpoint: API endpoint path
            params: Query parameters
            method: HTTP method
            
        Returns:
            JSON response data
            
        Raises:
            APIError: If the request fails
            AuthenticationError: If API key is invalid
            RateLimitError: If rate limit is exceeded
        """
        url = f"{self.config.base_url}{endpoint}"
        
        # Add API key to parameters
        params = params or {}
        params["api_key"] = self.config.api_key
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                timeout=self.config.timeout
            )
            
            # Handle specific HTTP status codes
            if response.status_code == 401:
                raise AuthenticationError(
                    "Invalid API key. Get your free key at https://api.nasa.gov/",
                    status_code=response.status_code
                )
            elif response.status_code == 429:
                raise RateLimitError(
                    "API rate limit exceeded. Please wait before making more requests.",
                    status_code=response.status_code
                )
            elif response.status_code == 400:
                try:
                    error_data = response.json()
                    error_msg = error_data.get("msg", "Bad request")
                except:
                    error_msg = "Bad request"
                raise APIError(
                    f"Bad request: {error_msg}",
                    status_code=response.status_code
                )
            elif not response.ok:
                raise APIError(
                    f"API request failed with status {response.status_code}: {response.text}",
                    status_code=response.status_code
                )
            
            return response.json()
            
        except requests.exceptions.Timeout:
            raise APIError("Request timed out")
        except requests.exceptions.ConnectionError:
            raise APIError("Failed to connect to NASA API")
        except requests.exceptions.RequestException as e:
            raise APIError(f"Request failed: {str(e)}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.session.close()
