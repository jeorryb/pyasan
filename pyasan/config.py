"""Configuration management for PyASAN."""

import os
from typing import Optional
from dotenv import load_dotenv

from .exceptions import ConfigurationError


class Config:
    """Configuration manager for NASA API credentials and settings."""

    def __init__(self, api_key: Optional[str] = None, load_env: bool = True):
        """
        Initialize configuration.

        Args:
            api_key: NASA API key. If not provided, will try to load from environment.
            load_env: Whether to load environment variables from .env file.
        """
        if load_env:
            load_dotenv()

        self._api_key = api_key or self._get_api_key_from_env()
        self.base_url = "https://api.nasa.gov"
        self.timeout = 15  # Reduced timeout to prevent hanging
        self.max_retries = 2  # Reduced retries for faster failure

    def _get_api_key_from_env(self) -> str:
        """Get API key from environment variables."""
        api_key = (
            os.getenv("NASA_API_KEY")
            or os.getenv("NASA_API_TOKEN")
            or "DEMO_KEY"  # NASA provides a demo key with limited requests
        )

        if api_key == "DEMO_KEY":
            import warnings

            warnings.warn(
                "Using DEMO_KEY. This has limited requests per hour. "
                "Get your free API key at https://api.nasa.gov/",
                UserWarning,
            )

        return api_key

    @property
    def api_key(self) -> str:
        """Get the NASA API key."""
        if not self._api_key:
            raise ConfigurationError(
                "NASA API key not found. Set NASA_API_KEY environment variable "
                "or pass api_key parameter. Get your free key at https://api.nasa.gov/"
            )
        return self._api_key

    @api_key.setter
    def api_key(self, value: str) -> None:
        """Set the NASA API key."""
        self._api_key = value
