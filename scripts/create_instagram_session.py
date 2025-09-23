#!/usr/bin/env python3
"""
Create Instagram Session

Run this script locally to create a valid Instagram session that can be used
by the automated posting script. This handles the 2FA challenge interactively.
"""

import os
import sys
from pathlib import Path

# Add the pyasan package to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from instagrapi import Client
except ImportError:
    print("❌ Missing instagrapi. Install with: pip install instagrapi")
    sys.exit(1)


def create_session():
    """Create an Instagram session interactively."""
    print("🔐 Instagram Session Creator")
    print("=" * 40)
    
    # Get credentials
    username = input("Instagram username: ").strip()
    password = input("Instagram password: ").strip()
    
    if not username or not password:
        print("❌ Username and password are required")
        return
    
    try:
        client = Client()
        
        print("\n📱 Logging into Instagram...")
        print("(This may require 2FA verification)")
        
        # This will handle 2FA interactively
        client.login(username, password)
        
        # Save session
        session_file = "instagram_session.json"
        client.dump_settings(session_file)
        
        print(f"✅ Successfully logged in and saved session to {session_file}")
        print("\n📋 Next steps:")
        print("1. Upload this session file to your server/GitHub environment")
        print("2. Update the automation script to use this session file")
        print("3. Keep this session file secure and private")
        
    except Exception as e:
        print(f"❌ Login failed: {e}")
        if "challenge" in str(e).lower():
            print("\n💡 Tips for 2FA issues:")
            print("- Make sure you have access to your email/phone for verification")
            print("- Try logging in through Instagram app first")
            print("- Consider using an app password if available")


if __name__ == "__main__":
    create_session()
