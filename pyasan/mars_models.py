"""Data models for NASA Mars Rover Photos API responses."""

from datetime import datetime
from datetime import date as date_type
from typing import List, Any
from enum import Enum
from pydantic import BaseModel, Field, field_validator


class RoverName(str, Enum):
    """Supported Mars rovers."""

    PERSEVERANCE = "perseverance"
    CURIOSITY = "curiosity"
    OPPORTUNITY = "opportunity"
    SPIRIT = "spirit"


class RoverStatus(str, Enum):
    """Rover mission status."""

    ACTIVE = "active"
    COMPLETE = "complete"


# Camera enums for different rovers
class PerseveranceCamera(str, Enum):
    """Perseverance rover cameras."""

    EDL_RUCAM = "EDL_RUCAM"
    EDL_RDCAM = "EDL_RDCAM"
    EDL_DDCAM = "EDL_DDCAM"
    EDL_PUCAM1 = "EDL_PUCAM1"
    EDL_PUCAM2 = "EDL_PUCAM2"
    NAVCAM_LEFT = "NAVCAM_LEFT"
    NAVCAM_RIGHT = "NAVCAM_RIGHT"
    MCZ_RIGHT = "MCZ_RIGHT"
    MCZ_LEFT = "MCZ_LEFT"
    FRONT_HAZCAM_LEFT_A = "FRONT_HAZCAM_LEFT_A"
    FRONT_HAZCAM_RIGHT_A = "FRONT_HAZCAM_RIGHT_A"
    REAR_HAZCAM_LEFT = "REAR_HAZCAM_LEFT"
    REAR_HAZCAM_RIGHT = "REAR_HAZCAM_RIGHT"
    SKYCAM = "SKYCAM"
    SHERLOC_WATSON = "SHERLOC_WATSON"


class CommonCamera(str, Enum):
    """Common cameras across rovers."""

    FHAZ = "FHAZ"  # Front Hazard Avoidance Camera
    RHAZ = "RHAZ"  # Rear Hazard Avoidance Camera
    MAST = "MAST"  # Mast Camera
    CHEMCAM = "CHEMCAM"  # Chemistry and Camera Complex
    MAHLI = "MAHLI"  # Mars Hand Lens Imager
    MARDI = "MARDI"  # Mars Descent Imager
    NAVCAM = "NAVCAM"  # Navigation Camera
    PANCAM = "PANCAM"  # Panoramic Camera
    MINITES = "MINITES"  # Miniature Thermal Emission Spectrometer


class Camera(BaseModel):
    """Camera information."""

    id: int = Field(..., description="Camera ID")
    name: str = Field(..., description="Camera name")
    rover_id: int = Field(..., description="Rover ID")
    full_name: str = Field(..., description="Full camera name")


class Rover(BaseModel):
    """Rover information."""

    id: int = Field(..., description="Rover ID")
    name: str = Field(..., description="Rover name")
    landing_date: date_type = Field(..., description="Landing date on Mars")
    launch_date: date_type = Field(..., description="Launch date from Earth")
    status: str = Field(..., description="Mission status")

    @field_validator("landing_date", "launch_date", mode="before")
    @classmethod
    def parse_date(cls, v: Any) -> date_type:
        """Parse date string to date object."""
        if isinstance(v, str):
            return datetime.strptime(v, "%Y-%m-%d").date()
        return v  # type: ignore


class MarsPhoto(BaseModel):
    """Mars rover photo."""

    id: int = Field(..., description="Photo ID")
    sol: int = Field(..., description="Martian sol (day)")
    camera: Camera = Field(..., description="Camera information")
    img_src: str = Field(..., description="Image source URL")
    earth_date: date_type = Field(..., description="Earth date when photo was taken")
    rover: Rover = Field(..., description="Rover information")

    @field_validator("earth_date", mode="before")
    @classmethod
    def parse_date(cls, v: Any) -> date_type:
        """Parse date string to date object."""
        if isinstance(v, str):
            return datetime.strptime(v, "%Y-%m-%d").date()
        return v  # type: ignore


class MarsPhotosResponse(BaseModel):
    """Response containing Mars rover photos."""

    photos: List[MarsPhoto] = Field(..., description="List of photos")

    def __len__(self) -> int:
        """Get the number of photos."""
        return len(self.photos)

    def __iter__(self) -> Any:
        """Iterate over photos."""
        return iter(self.photos)

    def __getitem__(self, index: int) -> MarsPhoto:
        """Get photo by index."""
        return self.photos[index]


class ManifestPhoto(BaseModel):
    """Photo information in mission manifest."""

    sol: int = Field(..., description="Martian sol")
    earth_date: date_type = Field(..., description="Earth date")
    total_photos: int = Field(..., description="Total photos taken on this sol")
    cameras: List[str] = Field(..., description="List of cameras used")

    @field_validator("earth_date", mode="before")
    @classmethod
    def parse_date(cls, v: Any) -> date_type:
        """Parse date string to date object."""
        if isinstance(v, str):
            return datetime.strptime(v, "%Y-%m-%d").date()
        return v  # type: ignore


class MissionManifest(BaseModel):
    """Mars rover mission manifest."""

    name: str = Field(..., description="Rover name")
    landing_date: date_type = Field(..., description="Landing date on Mars")
    launch_date: date_type = Field(..., description="Launch date from Earth")
    status: str = Field(..., description="Mission status")
    max_sol: int = Field(..., description="Maximum sol with photos")
    max_date: date_type = Field(..., description="Most recent Earth date with photos")
    total_photos: int = Field(..., description="Total number of photos")
    photos: List[ManifestPhoto] = Field(..., description="Photo information by sol")

    @field_validator("landing_date", "launch_date", "max_date", mode="before")
    @classmethod
    def parse_date(cls, v: Any) -> date_type:
        """Parse date string to date object."""
        if isinstance(v, str):
            return datetime.strptime(v, "%Y-%m-%d").date()
        return v  # type: ignore


class ManifestResponse(BaseModel):
    """Response containing mission manifest."""

    photo_manifest: MissionManifest = Field(..., description="Mission manifest")


# Camera mappings for each rover
ROVER_CAMERAS = {
    RoverName.PERSEVERANCE: [
        "EDL_RUCAM",
        "EDL_RDCAM",
        "EDL_DDCAM",
        "EDL_PUCAM1",
        "EDL_PUCAM2",
        "NAVCAM_LEFT",
        "NAVCAM_RIGHT",
        "MCZ_RIGHT",
        "MCZ_LEFT",
        "FRONT_HAZCAM_LEFT_A",
        "FRONT_HAZCAM_RIGHT_A",
        "REAR_HAZCAM_LEFT",
        "REAR_HAZCAM_RIGHT",
        "SKYCAM",
        "SHERLOC_WATSON",
    ],
    RoverName.CURIOSITY: [
        "FHAZ",
        "RHAZ",
        "MAST",
        "CHEMCAM",
        "MAHLI",
        "MARDI",
        "NAVCAM",
        "PANCAM",
        "MINITES",
    ],
    RoverName.OPPORTUNITY: ["FHAZ", "RHAZ", "NAVCAM", "PANCAM", "MINITES"],
    RoverName.SPIRIT: ["FHAZ", "RHAZ", "NAVCAM", "PANCAM", "MINITES"],
}
