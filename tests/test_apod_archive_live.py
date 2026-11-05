"""Live canary for the science.nasa.gov APOD archive parser.

These hit real NASA pages, so they are excluded from the normal test run. Run
them with ``pytest -m live``. A scheduled workflow does this weekly so that a
change in NASA's page markup is noticed before the daily Instagram post breaks.
"""

from datetime import date

import pytest

from pyasan.apod_archive import APODArchiveClient, is_placeholder

pytestmark = pytest.mark.live

APOD_ASSET_PATH = "/content/dam/science/cds/apod/"

# (day, expected title, expected media type). Chosen to cover each page shape
# the parser has to handle: old GIF, "Credit & Copyright", JPEG, recent, video.
KNOWN_DAYS = [
    (date(1995, 6, 16), "Neutron Star Earth", "image"),
    (date(1998, 11, 22), "The High Energy Crab Nebula", "image"),
    (date(2006, 5, 26), "Omega Centauri", "image"),
    (date(2019, 4, 10), "Martian Moon Phobos Crosses the Sun", "other"),
    (date(2024, 8, 20), "Supermoon Beyond the Temple of Poseidon", "image"),
    (date(2026, 1, 1), "Auroral Corona", "image"),
]


@pytest.fixture(scope="module")
def client():
    return APODArchiveClient()


@pytest.mark.parametrize("day,title,media_type", KNOWN_DAYS)
def test_known_day_parses(client, day, title, media_type):
    apod = client.get_apod(day)

    assert apod is not None, f"{day} page could not be fetched or parsed"
    assert apod.date == day
    assert apod.title == title
    assert apod.media_type == media_type
    assert apod.explanation, "explanation was empty"
    assert not is_placeholder(apod)
    if media_type == "image":
        assert APOD_ASSET_PATH in apod.url
        assert "?" not in apod.url


def test_random_pick_returns_real_image(client):
    apod = client.get_random_apod(max_attempts=20)

    assert apod is not None, "20 random dates produced no usable image"
    assert apod.is_image
    assert not is_placeholder(apod)
    assert APOD_ASSET_PATH in apod.url
