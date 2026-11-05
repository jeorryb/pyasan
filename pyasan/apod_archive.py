"""APOD archive client that reads science.nasa.gov directly.

NASA moved APOD to science.nasa.gov, and ``api.nasa.gov/planetary/apod`` now
returns a placeholder record (the NASA logo, titled "NASA Science") for archive
dates. ``apod.nasa.gov/apod/apYYMMDD.html`` still redirects to the real article
page for every date, so this client fetches that page and parses it.

Only the standard library is used for parsing.
"""

import random
import re
from datetime import date as date_type
from datetime import datetime
from html.parser import HTMLParser
from typing import Any, List, Optional

import requests

from .models import APODResponse

ARCHIVE_START = date_type(1995, 6, 16)
LEGACY_URL = "https://apod.nasa.gov/apod/ap{yymmdd}.html"

# Substrings that identify NASA's site chrome rather than a real APOD image.
_PLACEHOLDER_URL_MARKERS = ("nasa-logo", "news-thumbnail")
_PLACEHOLDER_TITLES = {"nasa science"}

_IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".gif")
_DASH = "[-\u2010-\u2015]"  # hyphen, en dash, em dash; NASA uses both
_TITLE_RE = re.compile(
    rf"APOD:\s*(\d{{4}} \w+ \d{{1,2}})\s*{_DASH}\s*(.+?)\s*{_DASH}\s*NASA Science"
)
_CREDIT_RE = re.compile(r"Credit(?:\s*&\s*Copyright)?:\s*(.+?)\s*(?:Authors\b|$)", re.S)


def is_placeholder(apod: APODResponse) -> bool:
    """Return True if ``apod`` is NASA's placeholder rather than a real picture."""
    if apod.title.strip().lower() in _PLACEHOLDER_TITLES:
        return True
    urls = [u for u in (apod.url, apod.hdurl, apod.thumbnail_url) if u]
    return any(marker in u.lower() for u in urls for marker in _PLACEHOLDER_URL_MARKERS)


class _ApodPageParser(HTMLParser):
    """Collect the pieces of an APOD article page we care about."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title_tag = ""
        self.hero_image: Optional[str] = None
        self.h1 = ""
        self.explanation = ""
        self.page_text: List[str] = []
        self._in_title = False
        self._in_h1 = False
        self._in_desc = False
        self._desc_depth = 0
        self._in_media = False
        self._media_depth = 0
        self._in_main = False

    @staticmethod
    def _classes(attrs: List[Any]) -> List[str]:
        return (dict(attrs).get("class") or "").split()

    def handle_starttag(self, tag: str, attrs: List[Any]) -> None:
        classes = self._classes(attrs)
        if tag == "title":
            self._in_title = True
        elif tag == "main":
            self._in_main = True
        elif tag == "h1" and self.h1 == "":
            self._in_h1 = True
        elif tag == "p" and "media-detail-hero__description" in classes:
            self._in_desc = True
            self._desc_depth = 1
        elif self._in_desc:
            self._desc_depth += 1 if tag == "p" else 0
        if "media-detail-hero__media" in classes:
            self._in_media = True
            self._media_depth = 1
        elif self._in_media:
            self._media_depth += 1 if tag == "div" else 0
            if tag == "a" and self.hero_image is None:
                href = dict(attrs).get("href") or ""
                if href.lower().split("?")[0].endswith(_IMAGE_EXTENSIONS):
                    self.hero_image = href

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False
        elif tag == "h1":
            self._in_h1 = False
        elif tag == "p" and self._in_desc:
            self._desc_depth -= 1
            if self._desc_depth <= 0:
                self._in_desc = False
        elif tag == "div" and self._in_media:
            self._media_depth -= 1
            if self._media_depth <= 0:
                self._in_media = False
        elif tag == "main":
            self._in_main = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title_tag += data
        if self._in_h1:
            self.h1 += data
        if self._in_desc:
            self.explanation += data
        if self._in_main:
            self.page_text.append(data)


def parse_apod_page(html: str, expected_date: date_type) -> Optional[APODResponse]:
    """Parse a science.nasa.gov APOD article page.

    Returns None when the page is not the APOD for ``expected_date`` (for
    example NASA's generic landing page, or a redirect to a different day).
    Pages without a still image come back with ``media_type="other"``.
    """
    parser = _ApodPageParser()
    parser.feed(html)

    match = _TITLE_RE.search(" ".join(parser.title_tag.split()))
    if not match:
        return None
    try:
        page_date = datetime.strptime(match.group(1), "%Y %B %d").date()
    except ValueError:
        return None
    if page_date != expected_date:
        return None

    title = " ".join(parser.h1.split()) or match.group(2)
    explanation = " ".join(parser.explanation.split())
    explanation = re.sub(r"^Explanation:\s*", "", explanation)

    text = " ".join(" ".join(parser.page_text).split())
    credit_match = _CREDIT_RE.search(text)
    credit = None
    if credit_match:
        credit = re.sub(r"\s+,", ",", " ".join(credit_match.group(1).split())) or None

    if parser.hero_image:
        image = parser.hero_image.split("?")[0]
        media_type, url, hdurl = "image", image, image
    else:
        media_type, url, hdurl = "other", LEGACY_URL.format(yymmdd=page_date.strftime("%y%m%d")), None

    return APODResponse(
        title=title,
        date=page_date,
        explanation=explanation,
        url=url,
        hdurl=hdurl,
        media_type=media_type,
        copyright=credit,
    )


class APODArchiveClient:
    """Fetch APOD entries straight from science.nasa.gov."""

    def __init__(
        self, session: Optional[requests.Session] = None, timeout: int = 30
    ) -> None:
        self.session = session or requests.Session()
        self.timeout = timeout

    def get_apod(self, day: date_type) -> Optional[APODResponse]:
        """Return the APOD for ``day``, or None if unavailable."""
        url = LEGACY_URL.format(yymmdd=day.strftime("%y%m%d"))
        try:
            response = self.session.get(url, timeout=self.timeout, allow_redirects=True)
        except requests.RequestException:
            return None
        if response.status_code != 200:
            return None
        return parse_apod_page(response.text, day)

    def _random_date(self, rng: Any) -> date_type:
        span = (date_type.today() - ARCHIVE_START).days
        return date_type.fromordinal(ARCHIVE_START.toordinal() + rng.randint(0, span))

    def get_random_apod(
        self, max_attempts: int = 10, rng: Optional[Any] = None
    ) -> Optional[APODResponse]:
        """Return a random real image APOD, or None after ``max_attempts``.

        Missing days, video days and placeholder entries are skipped.
        """
        rng = rng or random
        for _ in range(max_attempts):
            apod = self.get_apod(self._random_date(rng))
            if apod is not None and apod.is_image and not is_placeholder(apod):
                return apod
        return None
