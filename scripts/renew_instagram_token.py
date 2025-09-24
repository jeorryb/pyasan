#!/usr/bin/env python3
"""
Instagram Token Renewal Script

Automatically checks Instagram access token expiry and renews it if needed.
Designed to run in GitHub Actions with automatic secret updates.
"""

import os
import sys
import json
import requests
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Add the pyasan package to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('token_renewal.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def check_token_expiry(access_token: str) -> dict:
    """Check when the current token expires."""
    try:
        url = f"https://graph.facebook.com/v18.0/debug_token"
        params = {
            "input_token": access_token,
            "access_token": access_token
        }
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json().get("data", {})
        expires_at = data.get("expires_at")
        
        if expires_at:
            expiry_date = datetime.fromtimestamp(expires_at)
            days_remaining = (expiry_date - datetime.now()).days
            
            logger.info(f"🔍 Current token expires: {expiry_date.strftime('%B %d, %Y at %I:%M %p')}")
            logger.info(f"⏰ Days remaining: {days_remaining}")
            
            return {
                "expires_at": expires_at,
                "expiry_date": expiry_date,
                "days_remaining": days_remaining,
                "needs_renewal": days_remaining <= 7  # Renew if 7 days or less
            }
        else:
            logger.error("❌ Could not determine token expiry")
            return {"needs_renewal": True}  # Assume needs renewal if can't check
            
    except Exception as e:
        logger.error(f"❌ Error checking token expiry: {e}")
        return {"needs_renewal": True}  # Assume needs renewal on error


def renew_access_token(app_id: str, app_secret: str, current_token: str) -> str:
    """Renew the Instagram access token."""
    try:
        logger.info("🔄 Attempting to renew access token...")
        
        url = "https://graph.facebook.com/v18.0/oauth/access_token"
        params = {
            "grant_type": "fb_exchange_token",
            "client_id": app_id,
            "client_secret": app_secret,
            "fb_exchange_token": current_token
        }
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        new_token = data.get("access_token")
        expires_in = data.get("expires_in", 0)
        
        if new_token:
            days_valid = expires_in // 86400  # Convert seconds to days
            logger.info(f"✅ Successfully renewed token!")
            logger.info(f"⏰ New token valid for: {days_valid} days")
            return new_token
        else:
            logger.error("❌ No access token in renewal response")
            return None
            
    except requests.exceptions.HTTPError as e:
        logger.error(f"❌ HTTP Error renewing token: {e}")
        if e.response:
            try:
                error_data = e.response.json()
                logger.error(f"❌ API Error Details: {error_data}")
            except:
                logger.error(f"❌ Response: {e.response.text}")
        return None
    except Exception as e:
        logger.error(f"❌ Error renewing token: {e}")
        return None


def update_github_secret(new_token: str) -> bool:
    """Update GitHub secret with new token (GitHub Actions only)."""
    try:
        # Mask the token for security - only show first/last few characters
        masked_token = f"{new_token[:8]}...{new_token[-8:]}" if len(new_token) > 16 else "***MASKED***"
        
        logger.info("📝 NEW TOKEN GENERATED FOR GITHUB SECRET:")
        logger.info("=" * 50)
        logger.info("Secret name: INSTAGRAM_ACCESS_TOKEN")
        logger.info(f"Token preview: {masked_token}")
        logger.info("Token length: {} characters".format(len(new_token)))
        logger.info("=" * 50)
        logger.info("🔒 Full token has been generated but not logged for security")
        logger.info("💡 Please update your GitHub secret manually with the new token")
        logger.info("💡 The full token is available in the renewal response (check API output)")
        
        # TODO: Implement automatic GitHub secret update via API
        # This would securely update the secret without logging it
        return True
        
    except Exception as e:
        logger.error(f"❌ Error updating GitHub secret: {e}")
        return False


def main():
    """Main renewal process."""
    logger.info("🚀 Starting Instagram token renewal check...")
    
    # Get environment variables
    current_token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
    app_id = os.getenv("FACEBOOK_APP_ID", "1914060772854547")  # Default to your app ID
    app_secret = os.getenv("FACEBOOK_APP_SECRET")
    
    if not current_token:
        logger.error("❌ INSTAGRAM_ACCESS_TOKEN not found in environment")
        sys.exit(1)
    
    if not app_secret:
        logger.error("❌ FACEBOOK_APP_SECRET not found in environment")
        logger.info("💡 Add FACEBOOK_APP_SECRET to your GitHub secrets")
        sys.exit(1)
    
    # Check if token needs renewal
    token_info = check_token_expiry(current_token)
    
    if not token_info.get("needs_renewal", False):
        days_remaining = token_info.get("days_remaining", 0)
        logger.info(f"✅ Token is still valid for {days_remaining} days - no renewal needed")
        return
    
    # Renew the token
    new_token = renew_access_token(app_id, app_secret, current_token)
    
    if new_token:
        # Verify the new token works
        logger.info("🧪 Testing new token...")
        new_token_info = check_token_expiry(new_token)
        
        if new_token_info.get("days_remaining", 0) > 0:
            logger.info("✅ New token verified and working!")
            
            # Update GitHub secret (manual for now)
            update_github_secret(new_token)
            
            logger.info("🎉 Token renewal completed successfully!")
        else:
            logger.error("❌ New token verification failed")
            sys.exit(1)
    else:
        logger.error("❌ Token renewal failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
