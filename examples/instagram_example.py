#!/usr/bin/env python3
"""
Instagram APOD Example

Simple example showing how to fetch APOD data and prepare it for Instagram posting.
This is a test/demo version that doesn't actually post to Instagram.
"""

import os
import sys
from pathlib import Path

# Add the pyasan package to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pyasan import APODClient
from pyasan.exceptions import PyASANError


def create_instagram_caption(apod_data):
    """Create a sample Instagram caption."""
    title = apod_data.get("title", "Astronomy Picture of the Day")
    explanation = apod_data.get("explanation", "")
    date = apod_data.get("date", "Unknown")
    copyright_info = apod_data.get("copyright", "")

    # Truncate explanation for Instagram
    if len(explanation) > 1200:
        explanation = explanation[:1200] + "..."

    caption_parts = [
        f"🌟 {title}",
        f"📅 {date}",
        "",
        explanation,
        "",
    ]

    if copyright_info:
        caption_parts.extend(
            [
                f"📸 Credit: {copyright_info}",
                "",
            ]
        )

    caption_parts.extend(
        [
            "🚀 Brought to you by NASA's Astronomy Picture of the Day",
            "",
            "#NASA #APOD #astronomy #space #astrophotography #cosmos",
        ]
    )

    return "\n".join(caption_parts)


def main():
    """Main example function."""
    print("🚀 Instagram APOD Example")
    print("=" * 50)

    try:
        # Initialize APOD client
        api_key = os.getenv("NASA_API_KEY")  # Optional, will use DEMO_KEY if not set
        client = APODClient(api_key=api_key)

        # Get a random APOD
        print("📡 Fetching a random APOD...")
        apod = client.get_random_apod()

        print(f"✓ Title: {apod.title}")
        print(f"✓ Date: {apod.date}")
        print(f"✓ Media Type: {apod.media_type}")
        print(f"✓ URL: {apod.url}")

        if apod.media_type == "image":
            print("\n📱 Instagram Caption Preview:")
            print("-" * 50)

            caption_data = {
                "title": apod.title,
                "explanation": apod.explanation or "",
                "date": str(apod.date),
                "copyright": apod.copyright or "",
            }
            caption = create_instagram_caption(caption_data)

            print(caption)
            print("-" * 50)
            print(f"Caption length: {len(caption)} characters")

            if len(caption) > 2200:
                print("⚠️  Caption is too long for Instagram (max 2200 chars)")
            else:
                print("✅ Caption length is good for Instagram")

        else:
            print(f"⚠️  This APOD is a {apod.media_type}, not an image")
            print("   Instagram automation would fetch another random APOD")

        apod_date_str = str(apod.date).replace("-", "")
        apod_url = f"https://apod.nasa.gov/apod/ap{apod_date_str}.html"
        print(f"\n🔗 View full APOD at: {apod_url}")

    except PyASANError as e:
        print(f"❌ Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


if __name__ == "__main__":
    main()
