#!/usr/bin/env python3
"""
Generate a Long-Lived Instagram Access Token

This script helps you convert a short-lived token to a long-lived (60-day) token.
"""

import os
import sys
import requests
from pathlib import Path

# Add the pyasan package to the path
sys.path.insert(0, str(Path(__file__).parent.parent))


def exchange_for_long_lived_token(app_id: str, app_secret: str, short_lived_token: str) -> dict:
    """Exchange a short-lived token for a long-lived token (60 days)."""
    try:
        print("🔄 Exchanging short-lived token for long-lived token...")
        print()
        
        url = "https://graph.facebook.com/v18.0/oauth/access_token"
        params = {
            "grant_type": "fb_exchange_token",
            "client_id": app_id,
            "client_secret": app_secret,
            "fb_exchange_token": short_lived_token
        }
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        long_lived_token = data.get("access_token")
        expires_in = data.get("expires_in", 0)
        
        if long_lived_token:
            days_valid = expires_in // 86400  # Convert seconds to days
            
            print("✅ SUCCESS! Long-lived token generated!")
            print()
            print("=" * 70)
            print("📋 COPY THIS TOKEN TO YOUR GITHUB SECRETS:")
            print("=" * 70)
            print()
            print(f"{long_lived_token}")
            print()
            print("=" * 70)
            print(f"⏰ Token valid for: {days_valid} days (~{days_valid//30} months)")
            print("=" * 70)
            print()
            print("📝 NEXT STEPS:")
            print("1. Go to: https://github.com/YOUR_USERNAME/pyasan/settings/secrets/actions")
            print("2. Click on 'INSTAGRAM_ACCESS_TOKEN'")
            print("3. Click 'Update secret'")
            print("4. Paste the token shown above")
            print("5. Click 'Update secret' to save")
            print()
            print("💡 The renewal script will automatically refresh this token")
            print("   when it gets close to expiring (within 7 days).")
            print()
            
            return {
                "token": long_lived_token,
                "expires_in_days": days_valid,
                "success": True
            }
        else:
            print("❌ No access token in response")
            print(f"Response: {data}")
            return {"success": False, "error": "No token in response"}
            
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP Error: {e}")
        if e.response:
            try:
                error_data = e.response.json()
                print(f"❌ API Error Details: {error_data}")
                
                error_message = error_data.get("error", {}).get("message", "")
                if "expired" in error_message.lower():
                    print()
                    print("⚠️  YOUR TOKEN HAS EXPIRED!")
                    print("You need to generate a brand new token from Meta Developer Console.")
                elif "invalid" in error_message.lower():
                    print()
                    print("⚠️  YOUR TOKEN IS INVALID!")
                    print("Make sure you're using a valid User Access Token from Meta.")
                    
            except:
                print(f"❌ Response: {e.response.text}")
        return {"success": False, "error": str(e)}
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return {"success": False, "error": str(e)}


def verify_token(access_token: str) -> bool:
    """Verify the token works by checking debug info."""
    try:
        print("🔍 Verifying token...")
        
        url = f"https://graph.facebook.com/v18.0/debug_token"
        params = {
            "input_token": access_token,
            "access_token": access_token
        }
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json().get("data", {})
        
        if data.get("is_valid"):
            print("✅ Token is valid!")
            
            expires_at = data.get("expires_at")
            if expires_at:
                from datetime import datetime
                expiry_date = datetime.fromtimestamp(expires_at)
                print(f"📅 Expires: {expiry_date.strftime('%B %d, %Y at %I:%M %p')}")
            
            scopes = data.get("scopes", [])
            print(f"🔑 Scopes: {', '.join(scopes)}")
            
            return True
        else:
            print("❌ Token is not valid")
            return False
            
    except Exception as e:
        print(f"❌ Error verifying token: {e}")
        return False


def main():
    """Main process."""
    print("=" * 70)
    print("🔐 Instagram Long-Lived Token Generator")
    print("=" * 70)
    print()
    
    # Get credentials
    app_id = os.getenv("FACEBOOK_APP_ID", "1914060772854547")
    app_secret = os.getenv("FACEBOOK_APP_SECRET")
    short_lived_token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
    
    # Check for manual input if not in env
    if not app_secret:
        print("Enter your Facebook App Secret:")
        app_secret = input("> ").strip()
        
    if not short_lived_token:
        print()
        print("=" * 70)
        print("📝 HOW TO GET A SHORT-LIVED TOKEN:")
        print("=" * 70)
        print("1. Go to: https://developers.facebook.com/apps")
        print("2. Select your app")
        print("3. Go to: Graph API Explorer")
        print("4. Select your Instagram account")
        print("5. Add permissions: instagram_basic, instagram_content_publish")
        print("6. Click 'Generate Access Token'")
        print("7. Copy the token and paste it below")
        print("=" * 70)
        print()
        print("Paste your short-lived Instagram token:")
        short_lived_token = input("> ").strip()
    
    if not all([app_id, app_secret, short_lived_token]):
        print("❌ Missing required credentials")
        sys.exit(1)
    
    print()
    print("🔧 Configuration:")
    print(f"  App ID: {app_id}")
    print(f"  App Secret: {app_secret[:4]}...{app_secret[-4:]}")
    print(f"  Token: {short_lived_token[:15]}...")
    print()
    
    # First verify the short-lived token works
    if not verify_token(short_lived_token):
        print()
        print("❌ The token you provided is not valid or has expired.")
        print()
        print("💡 SOLUTION: Get a fresh token from Meta Developer Console")
        print("   1. Go to https://developers.facebook.com/tools/explorer/")
        print("   2. Generate a new User Access Token with required permissions")
        print("   3. Run this script again with the new token")
        print()
        sys.exit(1)
    
    print()
    
    # Exchange for long-lived token
    result = exchange_for_long_lived_token(app_id, app_secret, short_lived_token)
    
    if result.get("success"):
        # Verify the new long-lived token
        print("🧪 Verifying the long-lived token...")
        print()
        if verify_token(result["token"]):
            print()
            print("🎉 All done! Your long-lived token is ready to use!")
        sys.exit(0)
    else:
        print()
        print("❌ Failed to generate long-lived token")
        print()
        print("💡 TROUBLESHOOTING:")
        print("   • Make sure your token is not expired (get a fresh one)")
        print("   • Verify your App ID and App Secret are correct")
        print("   • Check that your app has Instagram Basic Display API enabled")
        print("   • Ensure your Instagram account is connected to your app")
        sys.exit(1)


if __name__ == "__main__":
    main()
