#!/bin/bash
# Instagram Credentials Setup Script
# This script helps you find and set up your Instagram credentials

set -e

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔐 Instagram Graph API Credentials Setup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "This script will help you:"
echo "  1. Generate or convert your access token"
echo "  2. Find your Instagram Business Account ID"
echo "  3. Verify your credentials"
echo "  4. Add them to GitHub Secrets"
echo ""

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: Please run this script from the pyasan project root"
    exit 1
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check dependencies
echo "📋 Checking dependencies..."
if ! command_exists curl; then
    echo "❌ curl is required but not installed"
    exit 1
fi

if ! command_exists python3; then
    echo "❌ python3 is required but not installed"
    exit 1
fi

echo "✅ All dependencies found"
echo ""

# Step 1: Get App Credentials
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📱 Step 1: Meta App Credentials"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "You need your Meta App credentials from:"
echo "🔗 https://developers.facebook.com/apps/"
echo ""
echo "Select your app → Settings → Basic"
echo ""

read -p "Enter your App ID: " APP_ID
if [ -z "$APP_ID" ]; then
    echo "❌ App ID is required"
    exit 1
fi

read -sp "Enter your App Secret: " APP_SECRET
echo ""
if [ -z "$APP_SECRET" ]; then
    echo "❌ App Secret is required"
    exit 1
fi

echo "✅ App credentials received"
echo ""

# Step 2: Get Access Token
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔑 Step 2: Access Token"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Choose an option:"
echo "  1. I have a short-lived token (expires in ~1 hour)"
echo "  2. I have a long-lived token (expires in ~60 days)"
echo "  3. I need help getting a token"
echo ""

read -p "Enter your choice (1-3): " TOKEN_CHOICE

if [ "$TOKEN_CHOICE" = "3" ]; then
    echo ""
    echo "📖 HOW TO GET YOUR ACCESS TOKEN:"
    echo ""
    echo "1. Go to Graph API Explorer:"
    echo "   🔗 https://developers.facebook.com/tools/explorer"
    echo ""
    echo "2. Select your app in the dropdown (top right)"
    echo ""
    echo "3. Click 'Permissions' (bottom left) and add:"
    echo "   ✓ instagram_basic"
    echo "   ✓ instagram_content_publish"
    echo "   ✓ pages_read_engagement"
    echo "   ✓ pages_show_list"
    echo ""
    echo "4. Click 'Generate Access Token'"
    echo ""
    echo "5. Copy the token and run this script again"
    echo ""
    exit 0
fi

read -sp "Paste your access token: " SHORT_TOKEN
echo ""

if [ -z "$SHORT_TOKEN" ]; then
    echo "❌ Token is required"
    exit 1
fi

LONG_TOKEN="$SHORT_TOKEN"

if [ "$TOKEN_CHOICE" = "1" ]; then
    echo ""
    echo "🔄 Converting to long-lived token..."
    
    RESPONSE=$(curl -s "https://graph.facebook.com/v20.0/oauth/access_token?grant_type=fb_exchange_token&client_id=$APP_ID&client_secret=$APP_SECRET&fb_exchange_token=$SHORT_TOKEN")
    
    if echo "$RESPONSE" | grep -q "access_token"; then
        LONG_TOKEN=$(echo "$RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
        EXPIRES_IN=$(echo "$RESPONSE" | grep -o '"expires_in":[0-9]*' | cut -d':' -f2)
        DAYS_VALID=$((EXPIRES_IN / 86400))
        
        echo "✅ Successfully converted to long-lived token!"
        echo "   Valid for: $DAYS_VALID days"
    else
        echo "❌ Failed to convert token:"
        echo "$RESPONSE"
        exit 1
    fi
fi

echo ""
echo "✅ Token ready (${#LONG_TOKEN} characters)"

# Save token for next steps
export INSTAGRAM_ACCESS_TOKEN="$LONG_TOKEN"

# Step 3: Find Instagram Account ID
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📱 Step 3: Finding Instagram Account ID"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Use venv python if available, otherwise use system python
if [ -f "venv/bin/python" ]; then
    PYTHON_CMD="venv/bin/python"
elif [ -f "venv/bin/python3" ]; then
    PYTHON_CMD="venv/bin/python3"
else
    PYTHON_CMD="python3"
fi

$PYTHON_CMD examples/find_instagram_id.py "$LONG_TOKEN"

# Ask if they want to verify
echo ""
read -p "📋 Did you find your Instagram Account ID? (y/n): " FOUND_ID

if [ "$FOUND_ID" != "y" ]; then
    echo ""
    echo "💡 Troubleshooting tips:"
    echo "   1. Make sure your Instagram is a BUSINESS account"
    echo "   2. Make sure it's linked to a Facebook Page"
    echo "   3. Check your token has all required permissions"
    echo ""
    echo "📚 See full guide: docs/FIND_INSTAGRAM_CREDENTIALS.md"
    exit 1
fi

read -p "Enter your Instagram Account ID: " ACCOUNT_ID

if [ -z "$ACCOUNT_ID" ]; then
    echo "❌ Account ID is required"
    exit 1
fi

# Step 4: Verify credentials
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 Step 4: Verifying Credentials"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

export INSTAGRAM_ACCOUNT_ID="$ACCOUNT_ID"

$PYTHON_CMD scripts/diagnose_instagram_token.py

# Step 5: Add to GitHub Secrets
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔐 Step 5: Add to GitHub Secrets"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if command_exists gh; then
    echo "✅ GitHub CLI detected!"
    echo ""
    read -p "Would you like to automatically add secrets using GitHub CLI? (y/n): " USE_GH_CLI
    
    if [ "$USE_GH_CLI" = "y" ]; then
        echo ""
        echo "Adding secrets..."
        
        echo "$LONG_TOKEN" | gh secret set INSTAGRAM_ACCESS_TOKEN
        echo "$ACCOUNT_ID" | gh secret set INSTAGRAM_ACCOUNT_ID
        echo "$APP_ID" | gh secret set FACEBOOK_APP_ID
        echo "$APP_SECRET" | gh secret set FACEBOOK_APP_SECRET
        
        echo "✅ All secrets added to GitHub!"
    else
        echo ""
        echo "📋 Add these secrets manually at:"
        echo "   🔗 https://github.com/jeorryb/pyasan/settings/secrets/actions"
        echo ""
        echo "Secrets to add:"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        echo "Name: INSTAGRAM_ACCESS_TOKEN"
        echo "Value: $LONG_TOKEN"
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        echo "Name: INSTAGRAM_ACCOUNT_ID"
        echo "Value: $ACCOUNT_ID"
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        echo "Name: FACEBOOK_APP_ID"
        echo "Value: $APP_ID"
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        echo "Name: FACEBOOK_APP_SECRET"
        echo "Value: $APP_SECRET"
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    fi
else
    echo "📋 Add these secrets manually at:"
    echo "   🔗 https://github.com/jeorryb/pyasan/settings/secrets/actions"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "INSTAGRAM_ACCESS_TOKEN = $LONG_TOKEN"
    echo "INSTAGRAM_ACCOUNT_ID = $ACCOUNT_ID"
    echo "FACEBOOK_APP_ID = $APP_ID"
    echo "FACEBOOK_APP_SECRET = $APP_SECRET"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 Setup Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🚀 Next steps:"
echo ""
echo "1. Test your workflow:"
if command_exists gh; then
    echo "   gh workflow run daily-apod-instagram.yml"
else
    echo "   Go to: https://github.com/jeorryb/pyasan/actions"
    echo "   Select 'Daily Random APOD Instagram Post'"
    echo "   Click 'Run workflow'"
fi
echo ""
echo "2. Monitor the results:"
echo "   https://github.com/jeorryb/pyasan/actions"
echo ""
echo "3. Your token expires in ~60 days. Set up automatic renewal:"
if command_exists gh; then
    echo "   gh workflow run renew-instagram-token.yml"
else
    echo "   The workflow runs automatically on the 1st of each month"
fi
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

