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

        # Initialize NASA APOD client
        logger.info("🔌 Connecting to NASA APOD API...")
        apod_client = APODClient(api_key=nasa_api_key)

        # Get a random APOD that is an image
        logger.info("📡 Fetching a random Astronomy Picture of the Day...")
        max_retries = 5
        apod = None

        for attempt in range(max_retries):
            apod = apod_client.get_random_apod()
            logger.info(f"✓ Retrieved APOD: {apod.title}")
            logger.info(f"  Date: {apod.date}")
            logger.info(f"  Media Type: {apod.media_type}")

            if apod.media_type == "image":
                break
            else:
                logger.info(
                    f"  Attempt {attempt + 1}: Got {apod.media_type}, trying again..."
                )

        # Check if we got an image
        if not apod or apod.media_type != "image":
            logger.warning(
                f"After {max_retries} attempts, couldn't find an image APOD. Skipping."
            )
            return

        if not apod.url:
            logger.error("❌ No image URL found in APOD data")
            sys.exit(1)

        # Use NASA's public image URL directly
        logger.info("🔗 Using NASA's public image URL...")

        # Prefer HD version if available, otherwise use regular URL
        public_image_url = apod.hdurl if apod.hdurl else apod.url

        if not public_image_url:
            logger.error("❌ No image URL found in APOD data")
            sys.exit(1)

        logger.info(f"✅ Using image URL: {public_image_url}")

        # Create caption
        logger.info("✍️ Creating Instagram caption...")
        caption = create_instagram_caption(
            {
                "title": apod.title,
                "explanation": apod.explanation or "",
                "date": str(apod.date),
                "copyright": apod.copyright or "",
            }
        )

        logger.info(f"📝 Caption preview: {caption[:100]}...")

        # Post to Instagram with retry for aspect ratio and other issues
        logger.info("📸 Posting to Instagram via Graph API...")
        post_id = None
        max_posting_attempts = 3  # Reduced from 7 to 3 - timing fix resolves most issues
        
        for posting_attempt in range(max_posting_attempts):
            logger.info(f"📸 Attempt {posting_attempt + 1}/{max_posting_attempts}: Posting to Instagram...")
            post_id = instagram_client.upload_image(public_image_url, caption)
            
            if post_id:
                logger.info("✅ Successfully posted random APOD to Instagram!")
                logger.info(f"📱 Post ID: {post_id}")
                break
            else:
                # If posting failed, try a different APOD
                if posting_attempt < max_posting_attempts - 1:
                    logger.warning(f"⚠️  Posting attempt {posting_attempt + 1} failed")
                    logger.info(f"🔄 Trying with a different random APOD... ({max_posting_attempts - posting_attempt - 1} attempts remaining)")
                    
                    # Brief delay to be respectful to the API
                    time.sleep(2)  # Reduced from 3s - timing issues now handled by processing delay
                    
                    # Get another random APOD
                    for retry_attempt in range(max_retries):
                        apod = apod_client.get_random_apod()
                        logger.info(f"✓ Retrieved new APOD: {apod.title} ({apod.date})")
                        
                        if apod.media_type == "image":
                            break
                    
                    if apod.media_type != "image":
                        logger.error("❌ Could not find another image APOD")
                        sys.exit(1)
                    
                    # Update image URL and caption for new APOD
                    public_image_url = apod.hdurl or apod.url
                    logger.info(f"✅ Using new image URL: {public_image_url}")
                    
                    caption = create_instagram_caption(
                        {
                            "title": apod.title,
                            "explanation": apod.explanation or "",
                            "date": str(apod.date),
                            "copyright": apod.copyright or "",
                        }
                    )
                    logger.info(f"📝 New caption preview: {caption[:100]}...")
                else:
                    logger.error("❌ Failed to post to Instagram after multiple attempts with random APODs")
                    logger.info("🎯 Trying one last time with today's APOD as fallback...")
                    
                    # Final fallback: try today's APOD
                    try:
                        today_apod = apod_client.get_apod()
                        if today_apod.media_type == "image":
                            logger.info(f"✓ Retrieved today's APOD: {today_apod.title}")
                            
                            public_image_url = today_apod.hdurl or today_apod.url
                            logger.info(f"✅ Using today's APOD image URL: {public_image_url}")
                            
                            caption = create_instagram_caption(
                                {
                                    "title": today_apod.title,
                                    "explanation": today_apod.explanation or "",
                                    "date": str(today_apod.date),
                                    "copyright": today_apod.copyright or "",
                                }
                            )
                            
                            logger.info("📸 Final attempt with today's APOD...")
                            final_post_id = instagram_client.upload_image(public_image_url, caption)
                            
                            if final_post_id:
                                logger.info("✅ Successfully posted today's APOD to Instagram!")
                                logger.info(f"📱 Post ID: {final_post_id}")
                                post_id = final_post_id
                            else:
                                logger.error("❌ Even today's APOD failed to post")
                                sys.exit(1)
                        else:
                            logger.error("❌ Today's APOD is not an image - complete failure")
                            sys.exit(1)
                    except Exception as fallback_error:
                        logger.error(f"❌ Fallback to today's APOD failed: {fallback_error}")
                        sys.exit(1)

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
