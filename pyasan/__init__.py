"""
PyASAN - A Python wrapper and CLI for NASA's REST APIs

This package provides a simple interface to interact with NASA's various APIs,
starting with the Astronomy Picture of the Day (APOD) API.
"""

__version__ = "0.3.1"
__author__ = "Jeorry Balasabas"
__email__ = "jeorry@gmail.com"

from .client import NASAClient
from .apod import APODClient
from .mars import MarsRoverPhotosClient

__all__ = ["NASAClient", "APODClient", "MarsRoverPhotosClient"]
