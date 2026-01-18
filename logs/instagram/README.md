# Instagram Posting Logs

This directory contains status information from the automated Instagram posting workflow.

## Files

- `last_successful_post.txt` - Updated after each successful Instagram post
  - Contains timestamp and run information
  - Helps keep the repository active to prevent workflow auto-disabling
  - GitHub disables scheduled workflows after 60 days of repository inactivity

## Purpose

GitHub Actions automatically disables scheduled workflows if there's no repository activity for 60 days. By committing this status file after each successful post, we ensure:

1. ✅ The repository stays active
2. 📊 We have an audit trail of successful posts
3. 🔄 The workflow continues running automatically

## Workflow

See `.github/workflows/daily-apod-instagram.yml` for the posting workflow implementation.
