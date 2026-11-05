"""APOD archive client that reads science.nasa.gov directly.

NASA moved APOD to science.nasa.gov, and ``api.nasa.gov/planetary/apod`` now
returns a placeholder record (the NASA logo, titled "NASA Science") for archive
dates. ``apod.nasa.gov/apod/apYYMMDD.html`` still redirects to the real article
page for every date, so this client fetches that page and parses it.

Parsing is deliberately layered: each field is read from the page's current
markup first and from independent fallbacks (stable URL paths, ``og:title``,
labelled text) if NASA renames CSS classes or tweaks titles. A page that
cannot be positively identified as the requested day is rejected, so a wrong
parse fails instead of posting something wrong.

Only the standard library is used for parsing.
"""

import random
import re
from datetime import date as date_type
from datetime import datetime
from html.parser import HTMLParser
from typing import Any, List, Optional, Tuple

import requests

from .models import APODResponse

ARCHIVE_START = date_type(1995, 6, 16)
LEGACY_URL = "https://apod.nasa.gov/apod/ap{yymmdd}.html"

# Substrings that identify NASA's site chrome rather than a real APOD image.
_PLACEHOLDER_URL_MARKERS = ("nasa-logo", "news-thumbnail")
_PLACEHOLDER_TITLES = {"nasa science"}

_IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".gif")
# APOD originals live under this path (resized copies use /dynamicimage/assets/).
_APOD_ASSET_PATH = "/science/cds/apod/"
_DYNAMIC_PREFIX = "/dynamicimage/assets/"
_ORIGINAL_PREFIX = "/content/dam/"

_DASH = "[-‐-―]"  # hyphen, en dash, em dash; NASA uses both
_TITLE_RE = re.compile(
    rf"APOD:\s*(\d{{4}} \w+ \d{{1,2}})\s*{_DASH}\s*(.+?)"
    rf"(?:\s*{_DASH}\s*NASA Science)?\s*$"
)
_BODY_DATE_RE = re.compile(r"\bDate:?\s+([A-Z][a-z]+ \d{1,2}, \d{4})")
_EXPLANATION_RE = re.compile(
    r"Explanation:\s*(.+?)\s*(?:\bDate:?\s+[A-Z][a-z]+ \d{1,2}, \d{4}|$)", re.S
)
_CREDIT_RE = re.compile(r"Credit(?:\s*&\s*Copyright)?:\s*(.+?)\s*(?:Authors\b|$)", re.S)


def is_placeholder(apod: APODResponse) -> bool:
    """Return True if ``apod`` is NASA's placeholder rather than a real picture."""
    if apod.title.strip().lower() in _PLACEHOLDER_TITLES:
        return True
    urls = [u for u in (apod.url, apod.hdurl, apod.thumbnail_url) if u]
    return any(marker in u.lower() for u in urls for marker in _PLACEHOLDER_URL_MARKERS)


def _original_apod_image(url: str) -> Optional[str]:
    """Return the original-resolution APOD image URL, or None if not an APOD image.

    Strips query strings and maps resized ``/dynamicimage/assets/`` URLs back to
    the ``/content/dam/`` original.
    """
    path = url.split("?")[0]
    if _APOD_ASSET_PATH not in path or not path.lower().endswith(_IMAGE_EXTENSIONS):
        return None
    return path.replace(_DYNAMIC_PREFIX, _ORIGINAL_PREFIX)


class _ApodPageParser(HTMLParser):
    """Collect every candidate for each field; the caller picks by priority."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title_tag = ""
        self.og_title = ""
        self.h1 = ""
        self.explanation = ""  # from the current description markup
        self.page_text: List[str] = []  # all text inside <main>
        self.hero_image: Optional[str] = None  # from the current media markup
        self.asset_links: List[str] = []  # APOD originals linked inside <main>
        self.asset_images: List[str] = []  # APOD images embedded inside <main>
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
        attr = {k: v or "" for k, v in attrs}
        if tag == "title":
            self._in_title = True
        elif tag == "meta" and attr.get("property") == "og:title":
            self.og_title = attr.get("content", "")
        elif tag == "main":
            self._in_main = True
        elif tag == "h1" and self.h1 == "":
            self._in_h1 = True
        elif tag == "p" and "media-detail-hero__description" in classes:
            self._in_desc = True
            self._desc_depth = 1
        elif self._in_desc and tag == "p":
            self._desc_depth += 1

        if "media-detail-hero__media" in classes:
            self._in_media = True
            self._media_depth = 1
        elif self._in_media and tag == "div":
            self._media_depth += 1

        if tag == "a":
            href = attr.get("href", "")
            if self._in_media and self.hero_image is None:
                if href.lower().split("?")[0].endswith(_IMAGE_EXTENSIONS):
                    self.hero_image = href
            if self._in_main and _original_apod_image(href):
                self.asset_links.append(href)
        elif tag == "img" and self._in_main:
            src = attr.get("src", "")
            if _original_apod_image(src):
                self.asset_images.append(src)

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


def _squash(text: str) -> str:
    return " ".join(text.split())


def _parse_title_and_date(
    parser: _ApodPageParser, body_text: str
) -> Tuple[Optional[date_type], Optional[str]]:
    """Find the page's date and title, trying each source in turn."""
    page_date: Optional[date_type] = None
    page_title: Optional[str] = None

    for source in (parser.title_tag, parser.og_title):
        match = _TITLE_RE.search(_squash(source))
        if not match:
            continue
        try:
            page_date = datetime.strptime(match.group(1), "%Y %B %d").date()
        except ValueError:
            continue
        page_title = match.group(2)
        break

    if page_date is None:
        # Titles unrecognised: fall back to the labelled date in the page body.
        match = _BODY_DATE_RE.search(body_text)
        if match:
            try:
                page_date = datetime.strptime(match.group(1), "%B %d, %Y").date()
            except ValueError:
                pass

    return page_date, page_title


def parse_apod_page(html: str, expected_date: date_type) -> Optional[APODResponse]:
    """Parse a science.nasa.gov APOD article page.

    Returns None when the page is not the APOD for ``expected_date`` (for
    example NASA's generic landing page, or a redirect to a different day).
    Pages without a still image come back with ``media_type="other"``.
    """
    parser = _ApodPageParser()
    parser.feed(html)
    body_text = _squash(" ".join(parser.page_text))

    page_date, title_from_meta = _parse_title_and_date(parser, body_text)
    if page_date is None or page_date != expected_date:
        return None

    title = _squash(parser.h1) or title_from_meta or ""
    if not title:
        return None

    explanation = _squash(parser.explanation)
    explanation = re.sub(r"^Explanation:\s*", "", explanation)
    if not explanation:
        match = _EXPLANATION_RE.search(body_text)
        explanation = match.group(1) if match else ""

    credit = None
    credit_match = _CREDIT_RE.search(body_text)
    if credit_match:
        credit = re.sub(r"\s+,", ",", _squash(credit_match.group(1))) or None

    # Image: current markup first, then APOD originals by path (links before
    # embedded images, since links point at the full-size file).
    image: Optional[str] = None
    if parser.hero_image:
        image = parser.hero_image.split("?")[0]
    else:
        candidates = parser.asset_links + parser.asset_images
        image = _original_apod_image(candidates[0]) if candidates else None

    if image:
        media_type, url, hdurl = "image", image, image
    else:
        media_type = "other"
        url = LEGACY_URL.format(yymmdd=page_date.strftime("%y%m%d"))
        hdurl = None

    return APODResponse(
        title=title,
        date=page_date,
        explanation=explanation,
        url=url,
        hdurl=hdurl,
        media_type=media_type,
        service_version=None,
        thumbnail_url=None,
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
