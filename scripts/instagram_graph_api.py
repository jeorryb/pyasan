#!/usr/bin/env python3
"""
Instagram Graph API APOD Poster

This script uses the official Meta Graph API to post random NASA APOD images
to Instagram using NASA's public image URLs directly. This is the recommended
approach for automated posting.

Requirements:
1. Facebook/Meta Developer Account
2. Instagram Business Account
3. Facebook Page connected to Instagram Business Account
4. App with Instagram Graph API permissions

Note: No image hosting required - uses NASA's public URLs directly!
"""

import os
import sys
import requests
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import logging

# Add the pyasan package to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pyasan import APODClient
from pyasan.apod_archive import APODArchiveClient, is_placeholder
from pyasan.models import APODResponse
from pyasan.exceptions import PyASANError

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("instagram_graph_api.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


class InstagramGraphAPI:
    """Instagram Graph API client for posting content."""

    def __init__(self, access_token: str, instagram_account_id: str):
        """
        Initialize Instagram Graph API client.

        Args:
            access_token: Long-lived access token for your app
            instagram_account_id: Instagram Business Account ID
        """
        self.access_token = access_token
        self.instagram_account_id = instagram_account_id
        self.base_url = "https://graph.facebook.com/v18.0"

    def upload_image(self, image_url: str, caption: str) -> Optional[str]:
        """
        Upload an image to Instagram.

        Args:
            image_url: Public URL of the image to post
            caption: Caption for the Instagram post

        Returns:
            Creation ID if successful, None otherwise
        """
        try:
            # Step 1: Create media object
            media_url = f"{self.base_url}/{self.instagram_account_id}/media"
            media_params = {
                "image_url": image_url,
                "caption": caption,
                "access_token": self.access_token,
            }

            logger.info("📤 Creating Instagram media object...")
            response = requests.post(media_url, data=media_params, timeout=30)
            
            # Log detailed error information if request fails
            if response.status_code != 200:
                try:
                    error_data = response.json()
                    logger.error(f"❌ API Error Details: {error_data}")
                except:
                    logger.error(f"❌ API Error: {response.status_code} - {response.text}")
            
            response.raise_for_status()

            media_data = response.json()
            creation_id = media_data.get("id")

            if not creation_id:
                logger.error("❌ Failed to get creation ID from media upload")
                return None

            logger.info(f"✅ Media object created with ID: {creation_id}")

            # Wait for Instagram to process the media (important for large images)
            logger.info("⏳ Waiting for Instagram to process the media...")
            time.sleep(3)  # Give Instagram time to process the media

            # Step 2: Publish the media
            publish_url = f"{self.base_url}/{self.instagram_account_id}/media_publish"
            publish_params = {
                "creation_id": creation_id,
                "access_token": self.access_token,
            }

            logger.info("📱 Publishing to Instagram...")
            publish_response = requests.post(
                publish_url, data=publish_params, timeout=30
            )
            
            # Log detailed error information for publish step if it fails
            if publish_response.status_code != 200:
                try:
                    error_data = publish_response.json()
                    logger.error(f"❌ Publish API Error Details: {error_data}")
                except:
                    logger.error(f"❌ Publish API Error: {publish_response.status_code} - {publish_response.text}")
            
            publish_response.raise_for_status()

            publish_data = publish_response.json()
            post_id = publish_data.get("id")

            if post_id:
                logger.info(
                    f"✅ Successfully published to Instagram! Post ID: {post_id}"
                )
                return post_id
            else:
                logger.error("❌ Failed to publish media")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ API request failed: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Upload failed: {e}")
            return None

    def get_account_info(self) -> Dict[str, Any]:
        """Get Instagram account information for verification."""
        try:
            url = f"{self.base_url}/{self.instagram_account_id}"
            params = {
                "fields": "id,username,media_count",
                "access_token": self.access_token,
            }

            response = requests.get(url, params=params, timeout=30)
            
            # Log detailed error information if request fails
            if response.status_code != 200:
                try:
                    error_data = response.json()
                    logger.error(f"❌ API Error Details: {error_data}")
                    # Check for specific error types
                    if "error" in error_data:
                        error_info = error_data["error"]
                        error_code = error_info.get("code", "unknown")
                        error_message = error_info.get("message", "unknown")
                        error_type = error_info.get("type", "unknown")
                        logger.error(f"❌ Error Code: {error_code}")
                        logger.error(f"❌ Error Type: {error_type}")
                        logger.error(f"❌ Error Message: {error_message}")
                        
                        # Provide helpful hints based on error
                        if error_code == 190:
                            logger.error("💡 Token error - your access token may be expired or invalid")
                            logger.error("💡 Run the token renewal workflow or check your INSTAGRAM_ACCESS_TOKEN secret")
                        elif error_code == 100:
                            logger.error("💡 Invalid parameter - check your INSTAGRAM_ACCOUNT_ID secret")
                            logger.error("💡 Make sure you're using your Instagram Business Account ID, not Page ID")
                except Exception as parse_error:
                    logger.error(f"❌ API Error: {response.status_code} - {response.text}")
            
            response.raise_for_status()

            return response.json()

        except Exception as e:
            logger.error(f"❌ Failed to get account info: {e}")
            return {}


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
    max_explanation_length = 1200
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

    # Add hashtags
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

    caption_parts.append(" ".join(hashtags[:25]))

    return "\n".join(caption_parts)


def is_postable(apod: APODResponse) -> bool:
    """True if the APOD is a real still image Instagram can accept."""
    if not apod.is_image or is_placeholder(apod):
        return False
    url = (apod.hdurl or apod.url or "").lower().split("?")[0]
    # Instagram's Graph API only accepts JPEG/PNG, not GIF.
    return bool(url) and not url.endswith(".gif")


def pick_random_apod(
    archive_client: APODArchiveClient, tried_urls: set, max_attempts: int = 10
) -> Optional[APODResponse]:
    """Pick a random postable APOD from the archive, skipping URLs already tried."""
    for _ in range(max_attempts):
        apod = archive_client.get_random_apod(max_attempts=5)
        if apod is None:
            continue
        if not is_postable(apod):
            logger.info(f"  Skipping {apod.date} ({apod.hdurl or apod.url})")
            continue
        if (apod.hdurl or apod.url) in tried_urls:
            continue
        logger.info(f"✓ Retrieved APOD: {apod.title}")
        logger.info(f"  Date: {apod.date}")
        return apod
    return None


def post_apod(instagram_client: "InstagramGraphAPI", apod: APODResponse) -> Optional[str]:
    """Build the caption for ``apod`` and post it. Returns the post ID or None."""
    image_url = apod.hdurl or apod.url
    logger.info(f"✅ Using image URL: {image_url}")
    caption = create_instagram_caption(
        {
            "title": apod.title,
            "explanation": apod.explanation or "",
            "date": str(apod.date),
            "copyright": apod.copyright or "",
        }
    )
    logger.info(f"📝 Caption preview: {caption[:100]}...")
    return instagram_client.upload_image(image_url, caption)


def main():
    """Main execution function."""
    logger.info("🚀 Starting Instagram Graph API APOD Poster")

    try:
        # Get required environment variables
        access_token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
        instagram_account_id = os.getenv("INSTAGRAM_ACCOUNT_ID")
        nasa_api_key = os.getenv("NASA_API_KEY")

        if not access_token:
            logger.error("❌ INSTAGRAM_ACCESS_TOKEN not found in environment")
            logger.error("💡 Get your token from Meta Developer Console")
            sys.exit(1)

        if not instagram_account_id:
            logger.error("❌ INSTAGRAM_ACCOUNT_ID not found in environment")
            logger.error(
                "💡 Get your Instagram Business Account ID from Graph API Explorer"
            )
            sys.exit(1)

        if not nasa_api_key:
            logger.warning("⚠️ NASA_API_KEY not found, using DEMO_KEY (rate limited)")

        # Initialize clients
        logger.info("🔌 Setting up Instagram Graph API client...")
        instagram_client = InstagramGraphAPI(access_token, instagram_account_id)

        # Verify account access
        logger.info("🔍 Verifying Instagram account access...")
        account_info = instagram_client.get_account_info()
        if account_info:
            username = account_info.get("username", "Unknown")
            media_count = account_info.get("media_count", 0)
            logger.info(
                f"✅ Connected to @{username} with {media_count} posts"
            )
        else:
            logger.error("❌ Failed to verify Instagram account access")
            sys.exit(1)

        # Initialize APOD clients.
        # The api.nasa.gov random endpoint currently returns NASA's logo as a
        # placeholder for archive dates, so random picks come from the
        # science.nasa.gov archive. The API is only used for today's APOD.
        logger.info("🔌 Connecting to NASA APOD sources...")
        archive_client = APODArchiveClient()
        apod_client = APODClient(api_key=nasa_api_key)

        max_posting_attempts = 3
        post_id = None
        tried_urls: set = set()

        for posting_attempt in range(max_posting_attempts):
            logger.info("📡 Fetching a random Astronomy Picture of the Day...")
            apod = pick_random_apod(archive_client, tried_urls)
            if apod is None:
                logger.warning("⚠️ Could not find a postable random APOD")
                continue

            logger.info(f"📸 Attempt {posting_attempt + 1}/{max_posting_attempts}: Posting to Instagram...")
            post_id = post_apod(instagram_client, apod)
            if post_id:
                break
            tried_urls.add(apod.hdurl or apod.url)
            time.sleep(2)

        if not post_id:
            logger.info("🎯 Falling back to today's APOD...")
            try:
                today_apod = apod_client.get_apod()
            except PyASANError as fallback_error:
                logger.error(f"❌ Fallback to today's APOD failed: {fallback_error}")
                today_apod = None

            if today_apod is not None and is_postable(today_apod):
                post_id = post_apod(instagram_client, today_apod)
            elif today_apod is not None:
                logger.error("❌ Today's APOD is not a postable image")

        if not post_id:
            # Fail loudly: a green run must mean a real post went out.
            logger.error("❌ No valid APOD could be posted to Instagram")
            sys.exit(1)

        logger.info("✅ Successfully posted APOD to Instagram!")
        logger.info(f"📱 Post ID: {post_id}")

        # No cleanup needed since we didn't download any files
        logger.info("🧹 No temporary files to clean up")

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
