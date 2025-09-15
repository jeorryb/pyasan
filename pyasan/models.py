"""Data models for NASA API responses."""

from datetime import datetime
from datetime import date as date_type
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


class APODResponse(BaseModel):
    """Model for APOD API response."""

    title: str = Field(..., description="The title of the image")
    date: date_type = Field(..., description="The date of the image")
    explanation: str = Field(..., description="The explanation of the image")
    url: str = Field(..., description="The URL of the image")
    media_type: str = Field(..., description="The type of media (image or video)")
    service_version: Optional[str] = Field(None, description="The service version")
    hdurl: Optional[str] = Field(None, description="The URL of the HD image")
    thumbnail_url: Optional[str] = Field(None, description="The URL of the thumbnail")
    copyright: Optional[str] = Field(None, description="The copyright information")

    @field_validator("date", mode="before")
    @classmethod
    def parse_date(cls, v):
        """Parse date string to date object."""
        if isinstance(v, str):
            return datetime.strptime(v, "%Y-%m-%d").date()
        return v

    @property
    def is_video(self) -> bool:
        """Check if the media is a video."""
        return self.media_type == "video"

    @property
    def is_image(self) -> bool:
        """Check if the media is an image."""
        return self.media_type == "image"


class APODBatch(BaseModel):
    """Model for batch APOD responses."""

    items: List[APODResponse] = Field(..., description="List of APOD responses")

    def __len__(self) -> int:
        """Get the number of items."""
        return len(self.items)

    def __iter__(self):
        """Iterate over items."""
        return iter(self.items)

    def __getitem__(self, index):
        """Get item by index."""
        return self.items[index]
