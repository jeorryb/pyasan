"""Tests for APOD selection and posting flow in scripts/instagram_graph_api.py."""

import importlib.util
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from pyasan.models import APODResponse

SCRIPT = Path(__file__).parent.parent / "scripts" / "instagram_graph_api.py"


@pytest.fixture(scope="module")
def script():
    spec = importlib.util.spec_from_file_location("instagram_graph_api", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def apod(url="https://assets.science.nasa.gov/a/real.jpg", **kw) -> APODResponse:
    data = dict(
        title="Real Title",
        date="2020-01-01",
        explanation="Because space.",
        url=url,
        hdurl=url,
        media_type="image",
    )
    data.update(kw)
    return APODResponse.model_validate(data)


LOGO = (
    "https://science.nasa.gov/wp-content/themes/nasa-child/assets/images/"
    "nasa-logo@2x.png"
)


class TestIsPostable:
    def test_jpeg_ok(self, script):
        assert script.is_postable(apod())

    def test_png_ok(self, script):
        assert script.is_postable(apod("https://x/y.png"))

    def test_gif_rejected(self, script):
        assert not script.is_postable(apod("https://x/y.gif"))

    def test_placeholder_rejected(self, script):
        assert not script.is_postable(apod(LOGO, title="NASA Science"))

    def test_non_image_rejected(self, script):
        assert not script.is_postable(apod(media_type="other"))


class TestPickRandomApod:
    def test_skips_unpostable_and_tried(self, script):
        archive = Mock()
        archive.get_random_apod.side_effect = [
            None,
            apod("https://x/anim.gif"),
            apod("https://x/tried.jpg"),
            apod("https://x/good.jpg"),
        ]
        picked = script.pick_random_apod(archive, {"https://x/tried.jpg"})
        assert picked.url == "https://x/good.jpg"

    def test_returns_none_when_nothing_postable(self, script):
        archive = Mock()
        archive.get_random_apod.return_value = None
        assert script.pick_random_apod(archive, set(), max_attempts=3) is None
        assert archive.get_random_apod.call_count == 3


class TestMain:
    @pytest.fixture
    def env(self, monkeypatch):
        monkeypatch.setenv("INSTAGRAM_ACCESS_TOKEN", "tok")
        monkeypatch.setenv("INSTAGRAM_ACCOUNT_ID", "123")
        monkeypatch.setenv("NASA_API_KEY", "key")

    def run_main(self, script, archive_apods, today, upload_results):
        ig = Mock()
        self.ig = ig
        ig.get_account_info.return_value = {"username": "u", "media_count": 1}
        ig.upload_image.side_effect = upload_results
        archive = Mock()
        archive.get_random_apod.side_effect = archive_apods
        api = Mock()
        if isinstance(today, Exception):
            api.get_apod.side_effect = today
        else:
            api.get_apod.return_value = today
        with patch.object(script, "InstagramGraphAPI", return_value=ig), patch.object(
            script, "APODArchiveClient", return_value=archive
        ), patch.object(script, "APODClient", return_value=api), patch.object(
            script.time, "sleep"
        ):
            script.main()
        return ig

    def test_posts_random_archive_apod(self, script, env):
        ig = self.run_main(script, [apod("https://x/a.jpg")], None, ["post-1"])
        assert ig.upload_image.call_args[0][0] == "https://x/a.jpg"

    def test_never_posts_placeholder(self, script, env):
        placeholder = apod(LOGO, title="NASA Science")
        with pytest.raises(SystemExit) as exc:
            self.run_main(script, [placeholder] * 100, placeholder, [])
        assert exc.value.code == 1
        self.ig.upload_image.assert_not_called()

    def test_falls_back_to_today_when_posting_fails(self, script, env):
        today = apod("https://x/today.jpg")
        ig = self.run_main(
            script,
            [apod(f"https://x/{i}.jpg") for i in range(3)],
            today,
            [None, None, None, "post-today"],
        )
        assert ig.upload_image.call_args[0][0] == "https://x/today.jpg"

    def test_exits_nonzero_when_everything_fails(self, script, env):
        with pytest.raises(SystemExit) as exc:
            self.run_main(
                script,
                [apod(f"https://x/{i}.jpg") for i in range(3)],
                apod("https://x/today.jpg"),
                [None, None, None, None],
            )
        assert exc.value.code == 1
