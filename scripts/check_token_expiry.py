#!/usr/bin/env python3
"""
Instagram Token Expiry Checker

Exits non-zero if the token is expired or has fewer than WARNING_DAYS remaining.
Used as a pre-flight check in the daily APOD workflow.
"""

import os
import sys
import requests
from datetime import datetime

WARNING_DAYS = 7  # Warn (and fail the job) when this many days remain


def check_token(access_token: str) -> int:
    """Return days remaining, or -1 if expired/invalid."""
    try:
        response = requests.get(
            "https://graph.facebook.com/v18.0/debug_token",
            params={"input_token": access_token, "access_token": access_token},
            timeout=30,
        )
        response.raise_for_status()
        data = response.json().get("data", {})

        if not data.get("is_valid"):
            return -1

        expires_at = data.get("expires_at")
        if not expires_at:
            return -1

        expiry_date = datetime.fromtimestamp(expires_at)
        days_remaining = (expiry_date - datetime.now()).days
        return days_remaining

    except requests.exceptions.HTTPError as e:
        if e.response is not None and e.response.status_code in (400, 401, 403):
            # Token is expired or invalid — the API itself rejects it
            return -1
        raise


def main():
    token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
    if not token:
        print("❌ INSTAGRAM_ACCESS_TOKEN not set")
        sys.exit(1)

    try:
        days = check_token(token)
    except Exception as e:
        print(f"❌ Error checking token: {e}")
        sys.exit(1)

    repo = os.getenv("GITHUB_REPOSITORY", "your-repo")
    bootstrap_url = f"https://github.com/{repo}/actions/workflows/bootstrap-instagram-token.yml"

    if days < 0:
        print("::error::❌ INSTAGRAM TOKEN IS EXPIRED")
        print(f"::error::Bootstrap a new token at: {bootstrap_url}")
        print("::error::  → Run workflow → paste a fresh short-lived token from")
        print("::error::    https://developers.facebook.com/tools/explorer/")
        sys.exit(1)

    print(f"✅ Token valid — {days} days remaining (expires {datetime.now().replace(microsecond=0)})")

    if days <= WARNING_DAYS:
        print(f"::warning::⚠️  Token expires in {days} day(s) — renewal should trigger today")
        print(f"::warning::If renewal keeps failing, bootstrap manually: {bootstrap_url}")
        # Still exit non-zero so the daily job fails and sends a notification
        sys.exit(1)


if __name__ == "__main__":
    main()
