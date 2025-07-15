# TempTrack Deployment Guide

## Files to Download for GitHub

### Required Files (9 files):
1. `app.py` - Main application
2. `cycle_analyzer.py` - Cycle analysis logic
3. `data_manager.py` - Backup data handling
4. `sqlite_storage.py` - SQLite database storage (NEW - fixes mobile data loss)
5. `graph_utils.py` - Chart generation
6. `requirements.txt` - Python dependencies
7. `README.md` - Project documentation
8. `config.toml` - Streamlit configuration
9. `DEPLOYMENT_GUIDE.md` - This guide

### GitHub Folder Structure
Since GitHub web interface doesn't allow folder uploads, create the `.streamlit` folder like this:

1. In your GitHub repo, click "Create new file"
2. Type `.streamlit/config.toml` as the filename
3. GitHub will create the folder automatically
4. Copy the contents of `config.toml` into this file

### Contents of .streamlit/config.toml:
```toml
[server]
headless = true
address = "0.0.0.0"
port = 5000

[theme]
primaryColor = "#FF6B6B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
```

## Mobile Data Loss Fix

The SQLite database storage should fix the mobile data loss issue you've been experiencing. The data now persists in a local database file instead of browser memory.

## Streamlit Cloud Deployment

1. Go to share.streamlit.io
2. Sign in with GitHub
3. Select your repository
4. Set main file: `app.py`
5. Deploy

## Important Notes

- Each user gets their own database file
- Data persists between app restarts
- Works better on mobile devices
- No external database required
- Compatible with Streamlit Cloud's free tier

## Troubleshooting

If you still experience data loss:
1. Check that `temptrack.db` file exists in the app
2. Look for database error messages in the app
3. Try clearing browser cache and reloading