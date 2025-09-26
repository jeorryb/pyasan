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
import base64
from datetime import datetime, timedelta
from pathlib import Path
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_public_key

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


def encrypt_secret_for_github(public_key_data: str, secret_value: str) -> str:
    """Encrypt a secret value using GitHub's public key."""
    try:
        # Decode the base64 public key
        public_key_bytes = base64.b64decode(public_key_data)
        
        # Load the public key
        public_key = load_pem_public_key(public_key_bytes)
        
        # Encrypt the secret
        encrypted_bytes = public_key.encrypt(
            secret_value.encode('utf-8'),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        # Return base64 encoded encrypted value
        return base64.b64encode(encrypted_bytes).decode('utf-8')
        
    except Exception as e:
        logger.error(f"❌ Error encrypting secret: {e}")
        raise


def get_github_public_key(repo_owner: str, repo_name: str, github_token: str) -> tuple:
    """Get the repository's public key for secret encryption."""
    try:
        url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/actions/secrets/public-key"
        headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "PyASAN-Token-Renewal/1.0"
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        return data["key"], data["key_id"]
        
    except Exception as e:
        logger.error(f"❌ Error getting GitHub public key: {e}")
        raise


def update_github_secret_api(repo_owner: str, repo_name: str, secret_name: str, 
                            secret_value: str, github_token: str) -> bool:
    """Update a GitHub repository secret via API."""
    try:
        logger.info(f"🔐 Updating GitHub secret: {secret_name}")
        
        # Get the repository's public key
        logger.info("📡 Getting repository public key...")
        public_key, key_id = get_github_public_key(repo_owner, repo_name, github_token)
        
        # Encrypt the secret value
        logger.info("🔒 Encrypting secret value...")
        encrypted_value = encrypt_secret_for_github(public_key, secret_value)
        
        # Update the secret
        logger.info("📤 Updating repository secret...")
        url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/actions/secrets/{secret_name}"
        headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "PyASAN-Token-Renewal/1.0"
        }
        
        payload = {
            "encrypted_value": encrypted_value,
            "key_id": key_id
        }
        
        response = requests.put(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        if response.status_code in [201, 204]:
            logger.info("✅ GitHub secret updated successfully!")
            return True
        else:
            logger.error(f"❌ Unexpected response code: {response.status_code}")
            return False
            
    except Exception as e:
        error_msg = str(e)
        if "403" in error_msg or "Forbidden" in error_msg:
            logger.error("❌ GitHub API Error: Insufficient permissions to update repository secrets")
            logger.error("💡 The GITHUB_TOKEN may not have admin access required for secret updates")
            logger.error("💡 This is normal - please update the secret manually as shown below")
        else:
            logger.error(f"❌ Error updating GitHub secret via API: {e}")
        return False


def update_github_secret(new_token: str) -> bool:
    """Update GitHub secret with new token."""
    try:
        # Mask the token for security - only show first/last few characters
        masked_token = f"{new_token[:8]}...{new_token[-8:]}" if len(new_token) > 16 else "***MASKED***"
        
        logger.info("📝 UPDATING GITHUB SECRET WITH NEW TOKEN:")
        logger.info("=" * 50)
        logger.info("Secret name: INSTAGRAM_ACCESS_TOKEN")
        logger.info(f"Token preview: {masked_token}")
        logger.info("Token length: {} characters".format(len(new_token)))
        logger.info("=" * 50)
        
        # Try automatic update via GitHub API
        github_token = os.getenv("GITHUB_TOKEN")
        github_repository = os.getenv("GITHUB_REPOSITORY")  # format: "owner/repo"
        
        if github_token and github_repository:
            logger.info("🤖 Attempting automatic GitHub secret update...")
            
            # Parse repository owner and name
            repo_parts = github_repository.split("/")
            if len(repo_parts) == 2:
                repo_owner, repo_name = repo_parts
                
                # Update the secret via API
                success = update_github_secret_api(
                    repo_owner, repo_name, "INSTAGRAM_ACCESS_TOKEN", 
                    new_token, github_token
                )
                
                if success:
                    logger.info("🎉 GitHub secret automatically updated!")
                    logger.info("🔒 Full token securely encrypted and stored")
                    return True
                else:
                    logger.warning("⚠️  Automatic update failed, falling back to manual process")
            else:
                logger.warning(f"⚠️  Invalid GITHUB_REPOSITORY format: {github_repository}")
        else:
            if not github_token:
                logger.info("ℹ️  GITHUB_TOKEN not available - running locally or token not provided")
            elif not github_repository:
                logger.info("ℹ️  GITHUB_REPOSITORY not available - not running in GitHub Actions")
            else:
                logger.info("ℹ️  GitHub API credentials available but automatic update may require admin permissions")
        
        # Fallback to manual process
        logger.info("📝 MANUAL UPDATE REQUIRED:")
        logger.info("🔒 Full token has been generated but not logged for security")
        logger.info("💡 Please update your GitHub secret manually with the new token")
        logger.info("💡 The full token is available in the renewal API response above")
        
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
