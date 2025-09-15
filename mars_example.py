#!/usr/bin/env python3
"""
Mars Rover Photos API Example - PyASAN

This script demonstrates how to use the PyASAN library to interact with NASA's
Mars Rover Photos API.
"""

from pyasan import MarsRoverPhotosClient
from pyasan.exceptions import PyASANError


def main():
    """Demonstrate Mars Rover Photos functionality."""
    print("🔴 PyASAN - Mars Rover Photos API Example\n")
    
    # Initialize the client (uses DEMO_KEY by default)
    # For production use, get your free API key at https://api.nasa.gov/
    client = MarsRoverPhotosClient()
    
    try:
        # Get available rovers
        print("🚀 Available Mars Rovers:")
        rovers = client.get_available_rovers()
        for rover in rovers:
            print(f"  • {rover.title()}")
        print()
        
        # Get Curiosity mission manifest
        print("📊 Getting Curiosity mission manifest...")
        manifest = client.get_manifest("curiosity")
        mission = manifest.photo_manifest
        print(f"Mission: {mission.name}")
        print(f"Status: {mission.status}")
        print(f"Landing Date: {mission.landing_date}")
        print(f"Total Photos: {mission.total_photos:,}")
        print(f"Max Sol: {mission.max_sol}")
        print()
        
        # Get available cameras for Curiosity
        print("📷 Curiosity Rover Cameras:")
        cameras = client.get_rover_cameras("curiosity")
        for camera in cameras[:5]:  # Show first 5
            print(f"  • {camera}")
        if len(cameras) > 5:
            print(f"  ... and {len(cameras) - 5} more")
        print()
        
        # Get photos from a specific sol
        print("📸 Getting photos from Curiosity Sol 1000 (MAST camera)...")
        photos = client.get_photos_by_sol("curiosity", sol=1000, camera="MAST")
        print(f"Found {len(photos)} photos from Sol 1000")
        if len(photos) > 0:
            photo = photos[0]  # Show first photo
            print(f"  Sample photo:")
            print(f"    ID: {photo.id}")
            print(f"    Earth Date: {photo.earth_date}")
            print(f"    Camera: {photo.camera.full_name}")
            print(f"    URL: {photo.img_src}")
        print()
        
        # Get photos by Earth date
        print("📅 Getting photos from Curiosity on 2015-05-30...")
        photos = client.get_photos_by_earth_date("curiosity", "2015-05-30", camera="FHAZ")
        print(f"Found {len(photos)} FHAZ photos from 2015-05-30")
        print()
        
        # Get latest photos (with timeout handling)
        print("🆕 Getting latest photos from Curiosity (safer with DEMO_KEY)...")
        try:
            latest = client.get_latest_photos("curiosity")
            print(f"Found {len(latest)} latest photos from Curiosity")
            if len(latest) > 0:
                photo = latest[0]
                print(f"  Latest photo:")
                print(f"    Sol: {photo.sol}")
                print(f"    Earth Date: {photo.earth_date}")
                print(f"    Camera: {photo.camera.full_name}")
        except Exception as e:
            print(f"  ⚠️  Could not fetch latest photos (likely rate limit): {e}")
        print()
        
        # Get Perseverance cameras
        print("📷 Perseverance Rover Cameras (sample):")
        perseverance_cameras = client.get_rover_cameras("perseverance")
        for camera in perseverance_cameras[:5]:
            print(f"  • {camera}")
        print()
        
        print("✅ All Mars rover examples completed successfully!")
        
    except PyASANError as e:
        print(f"❌ Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


if __name__ == "__main__":
    main()
