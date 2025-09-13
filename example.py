#!/usr/bin/env python3
"""
Example usage of PyASAN - NASA API Python wrapper.

This script demonstrates how to use the PyASAN library to interact with NASA's
Astronomy Picture of the Day (APOD) API.
"""

from pyasan import APODClient
from pyasan.exceptions import PyASANError


def main():
    """Demonstrate PyASAN functionality."""
    print("🚀 PyASAN - NASA API Python Wrapper Example\n")
    
    # Initialize the client (uses DEMO_KEY by default)
    # For production use, get your free API key at https://api.nasa.gov/
    client = APODClient()
    
    try:
        # Get today's APOD
        print("📅 Getting today's Astronomy Picture of the Day...")
        apod = client.get_apod(hd=True)
        print(f"Title: {apod.title}")
        print(f"Date: {apod.date}")
        print(f"Media Type: {apod.media_type}")
        print(f"URL: {apod.url}")
        if apod.hdurl:
            print(f"HD URL: {apod.hdurl}")
        if apod.copyright:
            print(f"Copyright: {apod.copyright}")
        print(f"Explanation: {apod.explanation[:100]}...")
        print()
        
        # Get a random APOD
        print("🎲 Getting a random APOD...")
        random_apod = client.get_random_apod()
        print(f"Random APOD: {random_apod.title} ({random_apod.date})")
        print()
        
        # Get multiple random APODs
        print("🎲 Getting 3 random APODs...")
        random_apods = client.get_random_apod(count=3)
        for i, apod in enumerate(random_apods, 1):
            print(f"{i}. {apod.title} ({apod.date})")
        print()
        
        # Get recent APODs
        print("📆 Getting recent APODs (last 5 days)...")
        recent = client.get_recent_apods(days=5)
        print(f"Found {len(recent)} recent APODs:")
        for apod in recent:
            print(f"  - {apod.date}: {apod.title}")
        print()
        
        # Get APOD for a specific date
        print("📅 Getting APOD for a specific date (2023-01-01)...")
        specific = client.get_apod(date="2023-01-01")
        print(f"New Year 2023 APOD: {specific.title}")
        print()
        
        print("✅ All examples completed successfully!")
        
    except PyASANError as e:
        print(f"❌ Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


if __name__ == "__main__":
    main()
