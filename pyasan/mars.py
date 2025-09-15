"""NASA Mars Rover Photos API client."""

from datetime import date as date_type, datetime
from typing import Optional, List, Union

from .client import NASAClient
from .config import Config
from .exceptions import ValidationError
from .mars_models import MarsPhotosResponse, ManifestResponse, RoverName, ROVER_CAMERAS


class MarsRoverPhotosClient(NASAClient):
    """Client for NASA's Mars Rover Photos API."""

    def __init__(self, api_key: Optional[str] = None, config: Optional[Config] = None):
        """
        Initialize Mars Rover Photos client.

        Args:
            api_key: NASA API key
            config: Configuration object
        """
        super().__init__(api_key=api_key, config=config)
        self.base_endpoint = "/mars-photos/api/v1"

    def get_photos(
        self,
        rover: Union[str, RoverName],
        sol: Optional[int] = None,
        earth_date: Optional[Union[str, date_type]] = None,
        camera: Optional[str] = None,
        page: Optional[int] = None,
    ) -> MarsPhotosResponse:
        """
        Get Mars rover photos.

        Args:
            rover: Rover name (perseverance, curiosity, opportunity, spirit)
            sol: Martian sol (day) - cannot be used with earth_date
            earth_date: Earth date in YYYY-MM-DD format - cannot be used with sol
            camera: Camera abbreviation (e.g., FHAZ, RHAZ, MAST, NAVCAM)
            page: Page number for pagination

        Returns:
            MarsPhotosResponse containing photos

        Raises:
            ValidationError: If parameters are invalid
            APIError: If the API request fails
        """
        rover_name = self._validate_rover(rover)

        # Validate that either sol or earth_date is provided, but not both
        if sol is not None and earth_date is not None:
            raise ValidationError("Cannot specify both sol and earth_date")

        if sol is None and earth_date is None:
            raise ValidationError("Must specify either sol or earth_date")

        params = {}

        if sol is not None:
            if sol < 0:
                raise ValidationError("Sol must be non-negative")
            params["sol"] = str(sol)

        if earth_date is not None:
            date_str = self._validate_and_format_date(earth_date)
            params["earth_date"] = date_str

        if camera is not None:
            camera_upper = camera.upper()
            if camera_upper not in ROVER_CAMERAS.get(RoverName(rover_name), []):
                valid_cameras = ", ".join(ROVER_CAMERAS.get(RoverName(rover_name), []))
                raise ValidationError(
                    f"Invalid camera '{camera}' for rover '{rover_name}'. "
                    f"Valid cameras: {valid_cameras}"
                )
            params["camera"] = camera_upper

        if page is not None:
            if page < 1:
                raise ValidationError("Page must be positive")
            params["page"] = str(page)

        endpoint = f"{self.base_endpoint}/rovers/{rover_name}/photos"
        response_data = self._make_request(endpoint, params)
        return MarsPhotosResponse(**response_data)

    def get_photos_by_sol(
        self,
        rover: Union[str, RoverName],
        sol: int,
        camera: Optional[str] = None,
        page: Optional[int] = None,
    ) -> MarsPhotosResponse:
        """
        Get Mars rover photos by Martian sol.

        Args:
            rover: Rover name
            sol: Martian sol (day)
            camera: Camera abbreviation (optional)
            page: Page number for pagination (optional)

        Returns:
            MarsPhotosResponse containing photos
        """
        return self.get_photos(rover=rover, sol=sol, camera=camera, page=page)

    def get_photos_by_earth_date(
        self,
        rover: Union[str, RoverName],
        earth_date: Union[str, date_type],
        camera: Optional[str] = None,
        page: Optional[int] = None,
    ) -> MarsPhotosResponse:
        """
        Get Mars rover photos by Earth date.

        Args:
            rover: Rover name
            earth_date: Earth date in YYYY-MM-DD format or date object
            camera: Camera abbreviation (optional)
            page: Page number for pagination (optional)

        Returns:
            MarsPhotosResponse containing photos
        """
        return self.get_photos(
            rover=rover, earth_date=earth_date, camera=camera, page=page
        )

    def get_latest_photos(self, rover: Union[str, RoverName]) -> MarsPhotosResponse:
        """
        Get the latest photos from a Mars rover.

        Args:
            rover: Rover name

        Returns:
            MarsPhotosResponse containing latest photos

        Raises:
            ValidationError: If rover name is invalid
            APIError: If the API request fails
        """
        rover_name = self._validate_rover(rover)

        endpoint = f"{self.base_endpoint}/rovers/{rover_name}/latest_photos"
        response_data = self._make_request(endpoint)

        # The latest_photos endpoint returns data in a different format
        if "latest_photos" in response_data:
            response_data["photos"] = response_data["latest_photos"]

        return MarsPhotosResponse(**response_data)

    def get_manifest(self, rover: Union[str, RoverName]) -> ManifestResponse:
        """
        Get mission manifest for a Mars rover.

        Args:
            rover: Rover name

        Returns:
            ManifestResponse containing mission information

        Raises:
            ValidationError: If rover name is invalid
            APIError: If the API request fails
        """
        rover_name = self._validate_rover(rover)

        endpoint = f"{self.base_endpoint}/manifests/{rover_name}"
        response_data = self._make_request(endpoint)
        return ManifestResponse(**response_data)

    def get_rover_cameras(self, rover: Union[str, RoverName]) -> List[str]:
        """
        Get list of available cameras for a rover.

        Args:
            rover: Rover name

        Returns:
            List of camera abbreviations

        Raises:
            ValidationError: If rover name is invalid
        """
        rover_name = self._validate_rover(rover)
        return ROVER_CAMERAS.get(RoverName(rover_name), [])

    def get_available_rovers(self) -> List[str]:
        """
        Get list of available rovers.

        Returns:
            List of rover names
        """
        return [rover.value for rover in RoverName]

    def _validate_rover(self, rover: Union[str, RoverName]) -> str:
        """
        Validate rover name.

        Args:
            rover: Rover name to validate

        Returns:
            Validated rover name in lowercase

        Raises:
            ValidationError: If rover name is invalid
        """
        if isinstance(rover, RoverName):
            return rover.value

        rover_lower = rover.lower()
        valid_rovers = [r.value for r in RoverName]

        if rover_lower not in valid_rovers:
            raise ValidationError(
                f"Invalid rover '{rover}'. Valid rovers: {', '.join(valid_rovers)}"
            )

        return rover_lower

    def _validate_and_format_date(self, date_input: Union[str, date_type]) -> str:
        """
        Validate and format date input.

        Args:
            date_input: Date as string or date object

        Returns:
            Formatted date string (YYYY-MM-DD)

        Raises:
            ValidationError: If date is invalid
        """
        if isinstance(date_input, date_type):
            date_obj = date_input
        elif isinstance(date_input, str):
            try:
                date_obj = datetime.strptime(date_input, "%Y-%m-%d").date()
            except ValueError:
                raise ValidationError(
                    f"Invalid date format: {date_input}. Use YYYY-MM-DD format."
                )
        else:
            raise ValidationError(
                f"Date must be a string or date object, got {type(date_input)}"
            )

        # Basic validation - Mars missions started in the 2000s
        min_date = date_type(2003, 1, 1)  # Before Spirit landing
        today = date_type.today()

        if date_obj < min_date:
            raise ValidationError(
                f"Date cannot be before {min_date} (before Mars rover missions)"
            )

        if date_obj > today:
            raise ValidationError("Date cannot be in the future")

        return date_obj.strftime("%Y-%m-%d")
