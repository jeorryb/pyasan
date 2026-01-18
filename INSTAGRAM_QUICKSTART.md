# Instagram Credentials Quick Start 🚀

Need to find your Instagram access token and account ID? Here's the fastest way!

## 🎯 The Fastest Method (Interactive Script)

Run this one command and follow the prompts:

```bash
cd /Users/jeorryb/pyasan
./scripts/setup_instagram_credentials.sh
```

This script will:
- ✅ Convert your short-lived token to a long-lived one
- ✅ Find your Instagram Business Account ID
- ✅ Verify everything works
- ✅ Optionally add secrets to GitHub automatically

---

## 📱 Manual Method (Step by Step)

### Step 1: Get Your Access Token

1. **Go to Graph API Explorer**
   - 🔗 https://developers.facebook.com/tools/explorer

2. **Select your app** (top right dropdown)

3. **Add permissions** (click "Permissions" button):
   - `instagram_basic`
   - `instagram_content_publish`
   - `pages_read_engagement`
   - `pages_show_list`

4. **Click "Generate Access Token"**

5. **Convert to long-lived token** (expires in 60 days):
   ```bash
   curl "https://graph.facebook.com/v20.0/oauth/access_token?grant_type=fb_exchange_token&client_id=YOUR_APP_ID&client_secret=YOUR_APP_SECRET&fb_exchange_token=YOUR_SHORT_TOKEN"
   ```
   
   Get your App ID and Secret from: https://developers.facebook.com/apps/ → Your App → Settings → Basic

### Step 2: Find Your Instagram Account ID

```bash
export INSTAGRAM_ACCESS_TOKEN="your_long_lived_token"
python examples/find_instagram_id.py
```

This will show your Instagram Business Account ID.

### Step 3: Verify Everything Works

```bash
export INSTAGRAM_ACCOUNT_ID="your_account_id"
python scripts/diagnose_instagram_token.py
```

You should see ✅ marks confirming everything is set up correctly.

### Step 4: Add to GitHub Secrets

Go to: https://github.com/jeorryb/pyasan/settings/secrets/actions

Add these secrets:
- `INSTAGRAM_ACCESS_TOKEN` = your long-lived token
- `INSTAGRAM_ACCOUNT_ID` = your Instagram Business Account ID
- `FACEBOOK_APP_ID` = your app ID
- `FACEBOOK_APP_SECRET` = your app secret

---

## ⚡ Super Quick Method (If you already have a token)

```bash
# Just pass your token directly
python examples/find_instagram_id.py YOUR_ACCESS_TOKEN
```

---

## 🛠️ Troubleshooting

### "No Instagram Business Account found"

**Problem**: Your Instagram is a Personal account, not Business

**Solution**:
1. Open Instagram app
2. Settings → Account → Switch to Professional Account
3. Choose "Business"
4. Link to a Facebook Page

### "Invalid OAuth access token"

**Problem**: Token expired or invalid

**Solution**: Generate a new token (see Step 1 above)

### "No Facebook Pages found"

**Problem**: No Facebook Page linked to your Instagram

**Solution**:
1. Create a Facebook Page: https://facebook.com/pages/create
2. Link to Instagram: Instagram → Settings → Account → Linked Accounts → Facebook

### Token expires every 60 days

**Solution**: Run the automatic renewal workflow monthly:
```bash
gh workflow run renew-instagram-token.yml
```

Or wait for it to run automatically on the 1st of each month.

---

## 📚 Detailed Guides

- **Full credentials guide**: [`docs/FIND_INSTAGRAM_CREDENTIALS.md`](docs/FIND_INSTAGRAM_CREDENTIALS.md)
- **Full setup guide**: [`docs/INSTAGRAM_GRAPH_API_SETUP.md`](docs/INSTAGRAM_GRAPH_API_SETUP.md)

---

## 🔍 Useful Commands

```bash
# Test your token validity
curl "https://graph.facebook.com/v20.0/debug_token?input_token=YOUR_TOKEN&access_token=YOUR_TOKEN"

# Get your account info
curl "https://graph.facebook.com/v20.0/YOUR_ACCOUNT_ID?fields=id,username,media_count&access_token=YOUR_TOKEN"

# List your Facebook pages
curl "https://graph.facebook.com/v20.0/me/accounts?access_token=YOUR_TOKEN"

# Get Instagram account from page
curl "https://graph.facebook.com/v20.0/PAGE_ID?fields=instagram_business_account&access_token=YOUR_TOKEN"
```

---

## 🎯 Current Status Check

Run this anytime to check your setup:

```bash
cd /Users/jeorryb/pyasan
export INSTAGRAM_ACCESS_TOKEN="your_token"
export INSTAGRAM_ACCOUNT_ID="your_id"
python scripts/diagnose_instagram_token.py
```

---

**Need more help?** Check the detailed guides in the `docs/` folder! 📖

