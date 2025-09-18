"""Data models for NASA TechTransfer API responses."""

from datetime import date as date_type, datetime
from typing import Optional, List, Any, Union
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class TechTransferCategory(str, Enum):
    """Categories for TechTransfer API endpoints."""

    PATENT = "patent"
    SOFTWARE = "software"
    SPINOFF = "spinoff"


class TechTransferPatent(BaseModel):
    """Model for TechTransfer Patent response."""

    id: Optional[str] = Field(None, description="Patent ID")
    title: str = Field(..., description="Patent title")
    abstract: Optional[str] = Field(None, description="Patent abstract")
    patent_number: Optional[str] = Field(None, description="Patent number")
    case_number: Optional[str] = Field(None, description="NASA case number")
    publication_date: Optional[date_type] = Field(None, description="Publication date")
    category: Optional[str] = Field(None, description="Technology category")
    center: Optional[str] = Field(None, description="NASA center")
    innovator: Optional[str] = Field(None, description="Inventor/innovator")
    contact: Optional[str] = Field(None, description="Contact information")

    @field_validator("publication_date", mode="before")
    @classmethod
    def parse_date(cls, v: Any) -> Optional[date_type]:
        """Parse date string to date object."""
        if v is None or v == "":
            return None
        if isinstance(v, str):
            # Try different date formats
            for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%Y"]:
                try:
                    return datetime.strptime(v, fmt).date()
                except ValueError:
                    continue
            # If no format works, return None
            return None
        return v


class TechTransferSoftware(BaseModel):
    """Model for TechTransfer Software response."""

    id: Optional[str] = Field(None, description="Software ID")
    title: str = Field(..., description="Software title")
    description: Optional[str] = Field(None, description="Software description")
    release_date: Optional[date_type] = Field(None, description="Release date")
    version: Optional[str] = Field(None, description="Software version")
    category: Optional[str] = Field(None, description="Technology category")
    center: Optional[str] = Field(None, description="NASA center")
    language: Optional[str] = Field(None, description="Programming language")
    license: Optional[str] = Field(None, description="License information")
    contact: Optional[str] = Field(None, description="Contact information")

    @field_validator("release_date", mode="before")
    @classmethod
    def parse_date(cls, v: Any) -> Optional[date_type]:
        """Parse date string to date object."""
        if v is None or v == "":
            return None
        if isinstance(v, str):
            # Try different date formats
            for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%Y"]:
                try:
                    return datetime.strptime(v, fmt).date()
                except ValueError:
                    continue
            return None
        return v


class TechTransferSpinoff(BaseModel):
    """Model for TechTransfer Spinoff response."""

    id: Optional[str] = Field(None, description="Spinoff ID")
    title: str = Field(..., description="Spinoff title")
    description: Optional[str] = Field(None, description="Spinoff description")
    publication_year: Optional[int] = Field(None, description="Publication year")
    category: Optional[str] = Field(None, description="Technology category")
    center: Optional[str] = Field(None, description="NASA center")
    company: Optional[str] = Field(None, description="Company name")
    state: Optional[str] = Field(None, description="State")
    benefits: Optional[str] = Field(None, description="Benefits description")
    applications: Optional[str] = Field(None, description="Applications")

    @field_validator("publication_year", mode="before")
    @classmethod
    def parse_year(cls, v: Any) -> Optional[int]:
        """Parse year string to integer."""
        if v is None or v == "":
            return None
        if isinstance(v, str):
            try:
                return int(v)
            except ValueError:
                return None
        return v


class TechTransferResponse(BaseModel):
    """Base model for TechTransfer API responses."""

    results: List[
        Union[TechTransferPatent, TechTransferSoftware, TechTransferSpinoff]
    ] = Field(..., description="List of technology transfer items")
    count: Optional[int] = Field(None, description="Total number of results")

    def __len__(self) -> int:
        """Get the number of results."""
        return len(self.results)

    def __iter__(self) -> Any:
        """Iterate over results."""
        return iter(self.results)

    def __getitem__(
        self, index: int
    ) -> Union[TechTransferPatent, TechTransferSoftware, TechTransferSpinoff]:
        """Get result by index."""
        return self.results[index]


class TechTransferPatentResponse(BaseModel):
    """Model for Patent API responses."""

    results: List[TechTransferPatent] = Field(..., description="List of patents")
    count: Optional[int] = Field(None, description="Total number of results")

    def __len__(self) -> int:
        """Get the number of patents."""
        return len(self.results)

    def __iter__(self) -> Any:
        """Iterate over patents."""
        return iter(self.results)

    def __getitem__(self, index: int) -> TechTransferPatent:
        """Get patent by index."""
        return self.results[index]


class TechTransferSoftwareResponse(BaseModel):
    """Model for Software API responses."""

    results: List[TechTransferSoftware] = Field(..., description="List of software")
    count: Optional[int] = Field(None, description="Total number of results")

    def __len__(self) -> int:
        """Get the number of software items."""
        return len(self.results)

    def __iter__(self) -> Any:
        """Iterate over software items."""
        return iter(self.results)

    def __getitem__(self, index: int) -> TechTransferSoftware:
        """Get software by index."""
        return self.results[index]


class TechTransferSpinoffResponse(BaseModel):
    """Model for Spinoff API responses."""

    results: List[TechTransferSpinoff] = Field(..., description="List of spinoffs")
    count: Optional[int] = Field(None, description="Total number of results")

    def __len__(self) -> int:
        """Get the number of spinoffs."""
        return len(self.results)

    def __iter__(self) -> Any:
        """Iterate over spinoffs."""
        return iter(self.results)

    def __getitem__(self, index: int) -> TechTransferSpinoff:
        """Get spinoff by index."""
        return self.results[index]
