#!/usr/bin/env python3
"""
Instagram Token Diagnostic Script

This script helps diagnose issues with your Instagram access token and account ID.
Run this to identify exactly what's wrong with your configuration.
"""

import os
import sys
import requests
from datetime import datetime

def test_access_token(token: str) -> dict:
    """Test if the access token is valid."""
    print("=" * 70)
    print("🔍 Testing Access Token Validity")
    print("=" * 70)
    
    # Test with debug_token endpoint
    url = "https://graph.facebook.com/v18.0/debug_token"
    params = {
        "input_token": token,
        "access_token": token
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if "data" in data:
                token_data = data["data"]
                print("✅ Token is valid!")
                print(f"   App ID: {token_data.get('app_id', 'N/A')}")
                print(f"   User ID: {token_data.get('user_id', 'N/A')}")
                print(f"   Is Valid: {token_data.get('is_valid', False)}")
                print(f"   Expires At: {token_data.get('expires_at', 'Never')}")
                
                if token_data.get('expires_at', 0) > 0:
                    expires_at = datetime.fromtimestamp(token_data['expires_at'])
                    days_remaining = (expires_at - datetime.now()).days
                    print(f"   Days Remaining: {days_remaining}")
                
                scopes = token_data.get('scopes', [])
                print(f"   Scopes: {', '.join(scopes) if scopes else 'None'}")
                
                return {"valid": True, "data": token_data}
            else:
                print("❌ Token data not found in response")
                return {"valid": False, "error": "No data in response"}
        else:
            error_data = response.json()
            print(f"❌ Token validation failed: {error_data}")
            return {"valid": False, "error": error_data}
            
    except Exception as e:
        print(f"❌ Error testing token: {e}")
        return {"valid": False, "error": str(e)}


def test_instagram_account(token: str, account_id: str) -> dict:
    """Test if the Instagram account ID is accessible."""
    print("\n" + "=" * 70)
    print("🔍 Testing Instagram Account Access")
    print("=" * 70)
    
    # Try different API versions
    api_versions = ["v18.0", "v19.0", "v20.0"]
    
    for version in api_versions:
        print(f"\nTrying API version: {version}")
        url = f"https://graph.facebook.com/{version}/{account_id}"
        params = {
            "fields": "id,username,media_count",
            "access_token": token
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Successfully accessed account with {version}!")
                print(f"   ID: {data.get('id', 'N/A')}")
                print(f"   Username: {data.get('username', 'N/A')}")
                print(f"   Media Count: {data.get('media_count', 'N/A')}")
                return {"accessible": True, "data": data, "version": version}
            else:
                try:
                    error_data = response.json()
                    print(f"❌ Failed with {version}")
                    if "error" in error_data:
                        error = error_data["error"]
                        print(f"   Error Code: {error.get('code', 'N/A')}")
                        print(f"   Error Type: {error.get('type', 'N/A')}")
                        print(f"   Error Message: {error.get('message', 'N/A')}")
                        
                        # Provide specific guidance based on error code
                        if error.get('code') == 190:
                            print("\n💡 DIAGNOSIS: Invalid or expired access token")
                            print("   → Your token needs to be renewed")
                            print("   → Run: gh workflow run renew-instagram-token.yml")
                        elif error.get('code') == 100:
                            print("\n💡 DIAGNOSIS: Invalid Instagram Account ID")
                            print("   → The account ID may be wrong")
                            print("   → Make sure you're using Instagram Business Account ID, not Page ID")
                        elif error.get('code') == 10:
                            print("\n💡 DIAGNOSIS: Permission denied")
                            print("   → Your token doesn't have required permissions")
                            print("   → Required: instagram_graph_user_profile, instagram_graph_user_media")
                except:
                    print(f"   Response: {response.text}")
                    
        except Exception as e:
            print(f"❌ Exception with {version}: {e}")
    
    return {"accessible": False, "error": "Failed with all API versions"}


def get_facebook_pages(token: str):
    """Get Facebook pages accessible with this token."""
    print("\n" + "=" * 70)
    print("🔍 Checking Facebook Pages")
    print("=" * 70)
    
    url = "https://graph.facebook.com/v18.0/me/accounts"
    params = {"access_token": token}
    
    try:
        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            pages = data.get("data", [])
            
            if pages:
                print(f"✅ Found {len(pages)} Facebook page(s):")
                for page in pages:
                    print(f"\n   Page: {page.get('name', 'N/A')}")
                    print(f"   ID: {page.get('id', 'N/A')}")
                    
                    # Try to get Instagram account for this page
                    page_id = page.get('id')
                    ig_url = f"https://graph.facebook.com/v18.0/{page_id}"
                    ig_params = {
                        "fields": "instagram_business_account",
                        "access_token": token
                    }
                    
                    try:
                        ig_response = requests.get(ig_url, params=ig_params, timeout=30)
                        if ig_response.status_code == 200:
                            ig_data = ig_response.json()
                            if "instagram_business_account" in ig_data:
                                ig_account = ig_data["instagram_business_account"]
                                print(f"   📸 Instagram Account ID: {ig_account.get('id')}")
                                print(f"   ✅ This is your INSTAGRAM_ACCOUNT_ID!")
                            else:
                                print(f"   ❌ No Instagram account linked to this page")
                    except Exception as e:
                        print(f"   ❌ Error getting Instagram account: {e}")
            else:
                print("❌ No Facebook pages found")
                print("💡 Your token may not have pages_show_list permission")
        else:
            error_data = response.json()
            print(f"❌ Failed to get pages: {error_data}")
            
    except Exception as e:
        print(f"❌ Error getting pages: {e}")


def main():
    """Run all diagnostics."""
    print("\n" + "=" * 70)
    print("🏥 Instagram Access Token & Account Diagnostic")
    print("=" * 70)
    print()
    
    # Get environment variables
    token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
    account_id = os.getenv("INSTAGRAM_ACCOUNT_ID")
    
    if not token:
        print("❌ INSTAGRAM_ACCESS_TOKEN not found in environment")
        print("💡 Set it with: export INSTAGRAM_ACCESS_TOKEN='your_token'")
        sys.exit(1)
    
    print(f"Token (first 20 chars): {token[:20]}...")
    print(f"Token length: {len(token)} characters")
    
    if account_id:
        print(f"Instagram Account ID: {account_id}")
    else:
        print("⚠️  INSTAGRAM_ACCOUNT_ID not set")
    
    # Run tests
    token_result = test_access_token(token)
    
    if token_result.get("valid"):
        # Test account access if ID is provided
        if account_id:
            account_result = test_instagram_account(token, account_id)
            
            if not account_result.get("accessible"):
                print("\n⚠️  Account not accessible, checking Facebook pages...")
                get_facebook_pages(token)
        else:
            print("\n⚠️  No account ID provided, checking Facebook pages...")
            get_facebook_pages(token)
    else:
        print("\n❌ Token is invalid, skipping further tests")
        print("\n💡 NEXT STEPS:")
        print("1. Check your token in GitHub Secrets")
        print("2. Run the token renewal workflow")
        print("3. Or generate a new token from Meta Developer Console")
    
    print("\n" + "=" * 70)
    print("Diagnostic complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()

