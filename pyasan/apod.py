"""NASA Astronomy Picture of the Day (APOD) API client."""

from datetime import datetime, timedelta
from datetime import date as date_type
from typing import Optional, Union

from .client import NASAClient
from .config import Config
from .exceptions import ValidationError
from .models import APODResponse, APODBatch


class APODClient(NASAClient):
    """Client for NASA's Astronomy Picture of the Day API."""

    def __init__(self, api_key: Optional[str] = None, config: Optional[Config] = None):
        """
        Initialize APOD client.

        Args:
            api_key: NASA API key
            config: Configuration object
        """
        super().__init__(api_key=api_key, config=config)
        self.endpoint = "/planetary/apod"

    def get_apod(
        self,
        date: Optional[Union[str, date_type]] = None,
        hd: bool = False,
        thumbs: bool = False,
    ) -> APODResponse:
        """
        Get Astronomy Picture of the Day for a specific date.

        Args:
            date: Date in YYYY-MM-DD format or date object. Defaults to today.
            hd: Return HD image URL if available
            thumbs: Return thumbnail URL for videos

        Returns:
            APODResponse object containing the APOD data

        Raises:
            ValidationError: If date is invalid
            APIError: If the API request fails
        """
        params = {}

        if date:
            date_str = self._validate_and_format_date(date)
            params["date"] = date_str

        if hd:
            params["hd"] = "true"

        if thumbs:
            params["thumbs"] = "true"

        response_data = self._make_request(self.endpoint, params)
        return APODResponse(**response_data)

    def get_random_apod(
        self, count: int = 1, hd: bool = False, thumbs: bool = False
    ) -> Union[APODResponse, APODBatch]:
        """
        Get random Astronomy Picture(s) of the Day.

        Args:
            count: Number of random images to retrieve (1-100)
            hd: Return HD image URLs if available
            thumbs: Return thumbnail URLs for videos

        Returns:
            APODResponse if count=1, APODBatch if count>1

        Raises:
            ValidationError: If count is invalid
            APIError: If the API request fails
        """
        if not 1 <= count <= 100:
            raise ValidationError("Count must be between 1 and 100")

        params = {"count": str(count)}

        if hd:
            params["hd"] = "true"

        if thumbs:
            params["thumbs"] = "true"

        response_data = self._make_request(self.endpoint, params)

        if count == 1:
            # API returns a single object for count=1
            if isinstance(response_data, list):
                response_data = response_data[0]
            return APODResponse.model_validate(response_data)
        else:
            # API returns a list for count>1
            items = [APODResponse.model_validate(item) for item in response_data]
            return APODBatch(items=items)

    def get_apod_range(
        self,
        start_date: Union[str, date_type],
        end_date: Union[str, date_type],
        hd: bool = False,
        thumbs: bool = False,
    ) -> APODBatch:
        """
        Get Astronomy Pictures of the Day for a date range.

        Args:
            start_date: Start date in YYYY-MM-DD format or date object
            end_date: End date in YYYY-MM-DD format or date object
            hd: Return HD image URLs if available
            thumbs: Return thumbnail URLs for videos

        Returns:
            APODBatch containing APOD data for the date range

        Raises:
            ValidationError: If date range is invalid
            APIError: If the API request fails
        """
        start_str = self._validate_and_format_date(start_date)
        end_str = self._validate_and_format_date(end_date)

        # Validate date range
        start_dt = datetime.strptime(start_str, "%Y-%m-%d").date()
        end_dt = datetime.strptime(end_str, "%Y-%m-%d").date()

        if start_dt > end_dt:
            raise ValidationError("start_date must be before or equal to end_date")

        # Check if range is too large (API limitation)
        days_diff = (end_dt - start_dt).days
        if days_diff > 100:
            raise ValidationError("Date range cannot exceed 100 days")

        params = {"start_date": start_str, "end_date": end_str}

        if hd:
            params["hd"] = "true"

        if thumbs:
            params["thumbs"] = "true"

        response_data = self._make_request(self.endpoint, params)
        items = [APODResponse.model_validate(item) for item in response_data]
        return APODBatch(items=items)

    def get_recent_apods(
        self, days: int = 7, hd: bool = False, thumbs: bool = False
    ) -> APODBatch:
        """
        Get recent Astronomy Pictures of the Day.

        Args:
            days: Number of recent days to retrieve (1-100)
            hd: Return HD image URLs if available
            thumbs: Return thumbnail URLs for videos

        Returns:
            APODBatch containing recent APOD data

        Raises:
            ValidationError: If days is invalid
        """
        if not 1 <= days <= 100:
            raise ValidationError("Days must be between 1 and 100")

        end_date = date_type.today()
        start_date = end_date - timedelta(days=days - 1)

        return self.get_apod_range(
            start_date=start_date, end_date=end_date, hd=hd, thumbs=thumbs
        )

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

        # Validate date range (APOD started on June 16, 1995)
        apod_start_date = date_type(1995, 6, 16)
        today = date_type.today()

        if date_obj < apod_start_date:
            raise ValidationError(
                f"Date cannot be before {apod_start_date} (APOD start date)"
            )

        if date_obj > today:
            raise ValidationError("Date cannot be in the future")

        return date_obj.strftime("%Y-%m-%d")
