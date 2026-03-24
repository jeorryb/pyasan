#!/usr/bin/env python3
"""
Quick Instagram Token Expiry Checker
"""

import os
import sys
import requests
from datetime import datetime

def check_token(access_token: str):
    """Check token expiry."""
    try:
        url = "https://graph.facebook.com/v18.0/debug_token"
        params = {
            "input_token": access_token,
            "access_token": access_token
        }
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json().get("data", {})
        
        print("=" * 70)
        print("🔍 Instagram Token Status")
        print("=" * 70)
        
        is_valid = data.get("is_valid")
        print(f"✅ Valid: {is_valid}")
        
        expires_at = data.get("expires_at")
        if expires_at:
            expiry_date = datetime.fromtimestamp(expires_at)
            now = datetime.now()
            days_remaining = (expiry_date - now).days
            hours_remaining = (expiry_date - now).seconds // 3600
            
            print(f"📅 Expires: {expiry_date.strftime('%B %d, %Y at %I:%M %p')}")
            print(f"⏰ Time remaining: {days_remaining} days, {hours_remaining} hours")
            print()
            
            if days_remaining >= 30:
                print("🎉 Great! You have a LONG-LIVED token (60-day)")
                print("   The renewal workflow will keep this fresh automatically.")
            elif days_remaining >= 1:
                print("⚠️  You have a SHORT-LIVED token!")
                print("   This will expire soon. Run: python scripts/get_new_long_lived_token.py")
            else:
                print("❌ Token expires in less than 1 day!")
                print("   Run: python scripts/get_new_long_lived_token.py IMMEDIATELY")
        else:
            print("❌ Could not determine expiry")
        
        scopes = data.get("scopes", [])
        if scopes:
            print(f"\n🔑 Permissions: {', '.join(scopes)}")
        
        print("=" * 70)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

def main():
    token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
    
    if not token:
        print("Enter your Instagram access token:")
        token = input("> ").strip()
    
    if not token:
        print("❌ No token provided")
        sys.exit(1)
    
    check_token(token)

if __name__ == "__main__":
    main()
