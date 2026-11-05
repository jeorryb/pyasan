"""Tests for the science.nasa.gov APOD archive client."""

import random
from datetime import date
from pathlib import Path
from unittest.mock import Mock

from pyasan.apod_archive import (
    APODArchiveClient,
    is_placeholder,
    parse_apod_page,
)
from pyasan.models import APODResponse

FIXTURES = Path(__file__).parent / "fixtures"
CRAB_TITLE_TAG = (
    "<title>APOD: 1998 November 22 - The High Energy Crab Nebula - NASA Science"
    "</title>"
)
LOGO_URL = (
    "https://science.nasa.gov/wp-content/themes/nasa-child/assets/images/"
    "nasa-logo@2x.png"
)


def fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf8")


def make_response(text: str, status: int = 200) -> Mock:
    resp = Mock()
    resp.status_code = status
    resp.text = text
    return resp


class TestParseApodPage:
    def test_old_archive_page(self):
        apod = parse_apod_page(fixture("apod_1998_11_22.html"), date(1998, 11, 22))
        assert apod is not None
        assert apod.title == "The High Energy Crab Nebula"
        assert apod.date == date(1998, 11, 22)
        assert apod.media_type == "image"
        assert apod.url == (
            "https://assets.science.nasa.gov/content/dam/science/cds/apod/apod/"
            "1998/november/crab_4wav_big.gif"
        )
        assert apod.hdurl == apod.url
        assert apod.explanation.startswith("This is the mess that is left")
        assert "Explanation:" not in apod.explanation
        assert "<a" not in apod.explanation
        assert apod.copyright == "G. Hennessy (USNO) et al., UIT, NASA"

    def test_recent_page_uses_original_not_resized_image(self):
        apod = parse_apod_page(fixture("apod_2026_11_05.html"), date(2026, 11, 5))
        assert apod is not None
        assert apod.title == "Enceladus in Silhouette"
        assert apod.url.endswith("/apod/2026/november/PIA17144EnceladusPandora.png")
        assert "dynamicimage" not in apod.url
        assert "?" not in apod.url
        assert apod.copyright == "Cassini Imaging Team, SSI, JPL, ESA, NASA"

    def test_credit_and_copyright_variant(self):
        html = fixture("apod_1998_11_22.html")
        marker = 'Credit: <a href="mailto:gsh@libra.usno.navy.mil">G. Hennessy</a>'
        assert marker in html
        html = html.replace(
            marker, 'Credit &amp; Copyright: <a href="#">Steve Crouch</a>'
        ).replace(
            ' (USNO) et al., UIT, <a href="http://www.nasa.gov/"'
            ' target="_blank">NASA</a>',
            "",
        )
        apod = parse_apod_page(html, date(1998, 11, 22))
        assert apod is not None and apod.copyright == "Steve Crouch"

    def test_generic_page_is_not_an_apod(self):
        assert parse_apod_page(fixture("apod_missing.html"), date(2026, 9, 30)) is None

    def test_date_mismatch_is_rejected(self):
        # Page is for 1998-11-22, but we asked for a different day.
        assert (
            parse_apod_page(fixture("apod_1998_11_22.html"), date(1998, 11, 23)) is None
        )

    def test_page_without_image_is_not_image(self):
        html = fixture("apod_1998_11_22.html")
        # Remove the hero image link so the page looks like a video day.
        html = html.replace("crab_4wav_big.gif", "watch")
        apod = parse_apod_page(html, date(1998, 11, 22))
        assert apod is not None
        assert apod.media_type != "image"


class TestIsPlaceholder:
    def _apod(self, **kw) -> APODResponse:
        data = dict(
            title="Real Title",
            date="2020-01-01",
            explanation="x",
            url="https://assets.science.nasa.gov/a/real.jpg",
            media_type="image",
        )
        data.update(kw)
        return APODResponse.model_validate(data)

    def test_real_image(self):
        assert not is_placeholder(self._apod())

    def test_logo_url(self):
        logo = "https://science.nasa.gov/x/nasa-logo@2x.png"
        assert is_placeholder(self._apod(url=logo, hdurl=logo))

    def test_logo_only_in_hdurl(self):
        logo = "https://science.nasa.gov/x/nasa-logo@2x.png"
        assert is_placeholder(self._apod(hdurl=logo))

    def test_generic_thumbnail(self):
        assert is_placeholder(self._apod(url="https://a/news-thumbnail.png"))

    def test_nasa_science_title(self):
        assert is_placeholder(self._apod(title="NASA Science"))

    def test_the_api_placeholder_record(self):
        logo = LOGO_URL
        assert is_placeholder(
            self._apod(title="NASA Science", url=logo, hdurl=logo, date="1998-11-22")
        )


class TestArchiveClient:
    def test_get_apod_builds_legacy_url_and_parses(self):
        session = Mock()
        session.get.return_value = make_response(fixture("apod_1998_11_22.html"))
        client = APODArchiveClient(session=session)

        apod = client.get_apod(date(1998, 11, 22))

        assert apod is not None and apod.title == "The High Energy Crab Nebula"
        assert session.get.call_args[0][0] == "https://apod.nasa.gov/apod/ap981122.html"

    def test_get_apod_http_error_returns_none(self):
        session = Mock()
        session.get.return_value = make_response("nope", status=404)
        assert APODArchiveClient(session=session).get_apod(date(2000, 1, 1)) is None

    def test_get_apod_network_error_returns_none(self):
        import requests

        session = Mock()
        session.get.side_effect = requests.ConnectionError("boom")
        assert APODArchiveClient(session=session).get_apod(date(2000, 1, 1)) is None

    def test_random_skips_missing_and_non_image_days(self):
        session = Mock()
        session.get.side_effect = [
            make_response(fixture("apod_missing.html")),
            make_response("nope", status=500),
            make_response(fixture("apod_1998_11_22.html")),
        ]
        client = APODArchiveClient(session=session)
        # Force every attempted date to be 1998-11-22 so the fixture matches.
        client._random_date = lambda rng: date(1998, 11, 22)

        apod = client.get_random_apod(max_attempts=5)

        assert apod is not None and apod.title == "The High Energy Crab Nebula"
        assert session.get.call_count == 3

    def test_random_gives_up_after_max_attempts(self):
        session = Mock()
        session.get.return_value = make_response(fixture("apod_missing.html"))
        client = APODArchiveClient(session=session)
        assert client.get_random_apod(max_attempts=3) is None
        assert session.get.call_count == 3

    def test_random_date_is_within_archive_range(self):
        client = APODArchiveClient(session=Mock())
        rng = random.Random(0)
        for _ in range(200):
            d = client._random_date(rng)
            assert date(1995, 6, 16) <= d <= date.today()


class TestParserResilience:
    """The parser should survive NASA renaming CSS classes or tweaking titles."""

    ORIG = (
        "https://assets.science.nasa.gov/content/dam/science/cds/apod/apod/"
        "1998/november/crab_4wav_big.gif"
    )

    def parse(self, html: str):
        return parse_apod_page(html, date(1998, 11, 22))

    def test_image_found_when_media_class_is_renamed(self):
        html = fixture("apod_1998_11_22.html").replace(
            "media-detail-hero__media", "renamed-media-wrapper"
        )
        apod = self.parse(html)
        assert apod is not None
        assert apod.media_type == "image"
        assert apod.url == self.ORIG

    def test_resized_image_normalised_to_original(self):
        html = fixture("apod_2026_11_05.html")
        html = html.replace("media-detail-hero__media", "renamed-media-wrapper")
        html = html.replace(
            '<a href="https://assets.science.nasa.gov/content/dam/science/cds/'
            'apod/apod/2026/november/PIA17144EnceladusPandora.png"',
            '<a href="#"',
        )
        apod = parse_apod_page(html, date(2026, 11, 5))
        assert apod is not None
        assert apod.url == (
            "https://assets.science.nasa.gov/content/dam/science/cds/apod/apod/"
            "2026/november/PIA17144EnceladusPandora.png"
        )

    def test_unrelated_site_images_are_not_mistaken_for_the_apod(self):
        html = fixture("apod_1998_11_22.html")
        html = html.replace("media-detail-hero__media", "renamed-media-wrapper")
        html = html.replace("cds/apod", "cds/other")
        apod = self.parse(html)
        assert apod is not None
        assert apod.media_type == "other"

    def test_explanation_found_when_description_class_is_renamed(self):
        html = fixture("apod_1998_11_22.html").replace(
            "media-detail-hero__description", "renamed-description"
        )
        apod = self.parse(html)
        assert apod is not None
        assert apod.explanation.startswith("This is the mess that is left")
        assert "Date November" not in apod.explanation

    def test_title_without_site_suffix(self):
        html = fixture("apod_1998_11_22.html").replace(
            " - NASA Science</title>", "</title>"
        )
        apod = self.parse(html)
        assert apod is not None
        assert apod.date == date(1998, 11, 22)

    def test_og_title_used_when_title_tag_is_unrecognised(self):
        html = fixture("apod_1998_11_22.html").replace(
            CRAB_TITLE_TAG,
            "<title>Something else entirely</title>"
            '<meta property="og:title" content="APOD: 1998 November 22 '
            '&#8211; The High Energy Crab Nebula - NASA Science">',
        )
        apod = self.parse(html)
        assert apod is not None
        assert apod.title == "The High Energy Crab Nebula"

    def test_date_taken_from_page_body_when_titles_are_unrecognised(self):
        html = fixture("apod_1998_11_22.html").replace(
            CRAB_TITLE_TAG,
            "<title>Something else entirely</title>",
        )
        apod = self.parse(html)
        assert apod is not None
        assert apod.date == date(1998, 11, 22)
        assert apod.title == "The High Energy Crab Nebula"

    def test_wrong_date_in_body_is_still_rejected(self):
        html = fixture("apod_1998_11_22.html").replace(
            CRAB_TITLE_TAG,
            "<title>Something else entirely</title>",
        )
        assert parse_apod_page(html, date(1998, 11, 23)) is None
