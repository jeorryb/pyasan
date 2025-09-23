#!/usr/bin/env python3
"""
Random APOD Instagram Poster

This script fetches a random NASA Astronomy Picture of the Day from the archives
and posts it to Instagram using the instagrapi library for reliable Instagram posting.
"""

import os
import sys
import tempfile
import requests
from datetime import datetime
from pathlib import Path
from typing import Optional
import logging

# Add the pyasan package to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pyasan import APODClient
from pyasan.exceptions import PyASANError

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("instagram_poster.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

try:
    from instagrapi import Client
    from PIL import Image
except ImportError as e:
    logger.error(
        "Missing required packages. Install with: pip install instagrapi pillow"
    )
    logger.error(f"Import error: {e}")
    sys.exit(1)


def setup_instagram_client() -> Optional[Client]:
    """
    Set up Instagram client with authentication.

    Returns:
        Authenticated Instagram client or None if setup fails
    """
    username = os.getenv("INSTAGRAM_USERNAME")
    password = os.getenv("INSTAGRAM_PASSWORD")

    if not username or not password:
        logger.error("Instagram credentials not found in environment variables")
        logger.error("Please set INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD")
        return None

    try:
        client = Client()

        # Try to load session if it exists (to avoid frequent logins)
        session_file = "/tmp/instagram_session.json"
        if os.path.exists(session_file):
            try:
                client.load_settings(session_file)
                client.login(username, password)
                logger.info("✓ Loaded existing Instagram session")
            except Exception as e:
                logger.warning(f"Failed to load session, creating new one: {e}")
                try:
                    client.login(username, password)
                    client.dump_settings(session_file)
                    logger.info("✓ Created new Instagram session")
                except Exception as login_error:
                    logger.error(f"Login failed: {login_error}")
                    if "challenge" in str(login_error).lower() or "code" in str(login_error).lower():
                        logger.error("Instagram requires 2FA verification. This cannot be automated.")
                        logger.error("Try logging in manually first, or use an app password if available.")
                    raise
        else:
            try:
                client.login(username, password)
                client.dump_settings(session_file)
                logger.info("✓ Created new Instagram session")
            except Exception as login_error:
                logger.error(f"Login failed: {login_error}")
                if "challenge" in str(login_error).lower() or "code" in str(login_error).lower():
                    logger.error("Instagram requires 2FA verification. This cannot be automated.")
                    logger.error("Try logging in manually first, or use an app password if available.")
                raise

        return client

    except Exception as e:
        logger.error(f"Failed to authenticate with Instagram: {e}")
        return None


def download_and_process_image(url: str, filename: str) -> str:
    """
    Download and process image for Instagram posting.

    Args:
        url: Image URL
        filename: Filename for the downloaded image

    Returns:
        Path to processed image file

    Raises:
        Exception: If download or processing fails
    """
    try:
        # Download image
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        # Create temporary file
        temp_dir = tempfile.gettempdir()
        original_path = os.path.join(temp_dir, f"original_{filename}")
        processed_path = os.path.join(temp_dir, f"processed_{filename}")

        with open(original_path, "wb") as f:
            f.write(response.content)

        logger.info(f"✓ Downloaded image to: {original_path}")

        # Process image for Instagram (ensure proper format and size)
        with Image.open(original_path) as img:
            # Convert to RGB if necessary
            if img.mode in ("RGBA", "LA", "P"):
                img = img.convert("RGB")

            # Instagram prefers square images, but we'll keep original aspect ratio
            # and let Instagram handle cropping if needed

            # Ensure image isn't too large (Instagram has size limits)
            max_size = 1080
            if img.width > max_size or img.height > max_size:
                img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                logger.info("✓ Resized image to fit Instagram limits")

            # Save as JPEG
            img.save(processed_path, "JPEG", quality=95, optimize=True)

        logger.info(f"✓ Processed image saved to: {processed_path}")

        # Clean up original
        try:
            os.remove(original_path)
        except Exception:
            pass

        return processed_path

    except Exception as e:
        raise Exception(f"Failed to download/process image: {str(e)}")


def create_instagram_caption(apod_data: dict) -> str:
    """
    Create Instagram caption from APOD data.

    Args:
        apod_data: APOD response data

    Returns:
        Formatted Instagram caption
    """
    title = apod_data.get("title", "Astronomy Picture of the Day")
    explanation = apod_data.get("explanation", "")
    date = apod_data.get("date", datetime.now().strftime("%Y-%m-%d"))
    copyright_info = apod_data.get("copyright", "")

    # Instagram caption limit is 2200 characters
    max_explanation_length = 1200  # Leave room for hashtags and other text
    if len(explanation) > max_explanation_length:
        explanation = explanation[:max_explanation_length].rsplit(" ", 1)[0] + "..."

    # Build caption
    caption_parts = [
        f"🌟 {title}",
        f"📅 {date}",
        "",
        explanation,
        "",
    ]

    # Add copyright if available
    if copyright_info:
        caption_parts.extend(
            [
                f"📸 Credit: {copyright_info}",
                "",
            ]
        )

    # Add source attribution
    caption_parts.extend(
        [
            "🚀 From NASA's Astronomy Picture of the Day archives",
            "🔗 https://apod.nasa.gov/apod/",
            "",
        ]
    )

    # Add hashtags (Instagram allows up to 30 hashtags)
    hashtags = [
        "#NASA",
        "#APOD",
        "#astronomy",
        "#space",
        "#astrophotography",
        "#cosmos",
        "#universe",
        "#science",
        "#telescope",
        "#hubble",
        "#jwst",
        "#spaceexploration",
        "#dailyastronomy",
        "#stars",
        "#galaxy",
        "#nebula",
        "#planet",
        "#solarsystem",
        "#astro",
        "#nightsky",
        "#deepspace",
        "#spaceart",
        "#astronomypic",
        "#nasapic",
        "#spacelove",
        "#stargazing",
        "#cosmology",
    ]

    caption_parts.append(" ".join(hashtags[:25]))  # Limit to 25 hashtags for safety

    return "\n".join(caption_parts)


def post_to_instagram(client: Client, image_path: str, caption: str) -> bool:
    """
    Post image to Instagram.

    Args:
        client: Authenticated Instagram client
        image_path: Path to image file
        caption: Instagram caption

    Returns:
        True if successful, False otherwise
    """
    try:
        # Upload photo
        media = client.photo_upload(image_path, caption)

        if media:
            logger.info(f"✅ Successfully posted to Instagram! Media ID: {media.id}")
            logger.info(f"📱 Post URL: https://www.instagram.com/p/{media.code}/")
            return True
        else:
            logger.error("❌ Failed to upload photo - no media object returned")
            return False

    except Exception as e:
        logger.error(f"❌ Failed to post to Instagram: {str(e)}")
        return False


def main():
    """Main execution function."""
    logger.info("🚀 Starting Random APOD Instagram Poster")

    try:
        # Set up Instagram client
        logger.info("📱 Setting up Instagram client...")
        instagram_client = setup_instagram_client()
        if not instagram_client:
            logger.error("Failed to set up Instagram client")
            sys.exit(1)

        # Get NASA API key from environment
        nasa_api_key = os.getenv("NASA_API_KEY")
        if not nasa_api_key:
            logger.warning("NASA_API_KEY not found, using DEMO_KEY (rate limited)")

        # Initialize APOD client
        logger.info("🔌 Connecting to NASA APOD API...")
        client = APODClient(api_key=nasa_api_key)

        # Get a random APOD that is an image (retry up to 5 times if we get videos)
        logger.info("📡 Fetching a random Astronomy Picture of the Day...")
        max_retries = 5
        apod = None

        for attempt in range(max_retries):
            apod = client.get_random_apod()
            logger.info(f"✓ Retrieved APOD: {apod.title}")
            logger.info(f"  Date: {apod.date}")
            logger.info(f"  Media Type: {apod.media_type}")

            if apod.media_type == "image":
                break
            else:
                logger.info(
                    f"  Attempt {attempt + 1}: Got {apod.media_type}, trying again..."
                )

        # Check if we finally got an image
        if not apod or apod.media_type != "image":
            logger.warning(
                f"After {max_retries} attempts, couldn't find an image APOD. "
                f"Skipping Instagram post."
            )
            return

        if not apod.url:
            logger.error("No image URL found in APOD data")
            sys.exit(1)

        # Download and process the image
        logger.info("⬇️  Downloading and processing image...")
        image_filename = f"apod_{str(apod.date).replace('-', '_')}.jpg"
        image_path = download_and_process_image(apod.url, image_filename)

        # Create Instagram caption
        logger.info("✍️  Creating Instagram caption...")
        caption = create_instagram_caption(
            {
                "title": apod.title,
                "explanation": apod.explanation,
                "date": str(apod.date),
                "copyright": apod.copyright,
            }
        )

        logger.info(f"📝 Caption preview: {caption[:100]}...")

        # Post to Instagram
        logger.info("📸 Posting to Instagram...")
        success = post_to_instagram(instagram_client, image_path, caption)

        if success:
            logger.info("✅ Successfully posted random APOD to Instagram!")
        else:
            logger.error("❌ Failed to post to Instagram")
            sys.exit(1)

        # Clean up temporary files
        try:
            os.remove(image_path)
            logger.info("🧹 Cleaned up temporary files")
        except Exception as e:
            logger.warning(f"Failed to clean up temporary file: {e}")

    except PyASANError as e:
        logger.error(f"❌ NASA API Error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        import traceback

        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
