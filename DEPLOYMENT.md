# GitHub Setup Instructions

## Step 1: Create GitHub Repository

1. Go to https://github.com and sign in
2. Click the "+" icon in the top right and select "New repository"
3. Repository name: `upwork-proposal-agent`
4. Description: `Gemini-powered Upwork proposal generator`
5. Make it **Public** (required for Streamlit Community Cloud free tier)
6. **DO NOT** initialize with README, .gitignore, or license (we already have these)
7. Click "Create repository"

## Step 2: Push Code to GitHub

Run these commands in your terminal (from the upwork-proposal-agent directory):

```bash
# Add the remote repository (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/upwork-proposal-agent.git

# Push to GitHub
git push -u origin main
```

## Step 3: Deploy to Streamlit Community Cloud

1. Go to https://streamlit.io/cloud
2. Click "Sign in" and connect your GitHub account
3. Click "New app" or "Deploy an app"
4. Select the `upwork-proposal-agent` repository
5. Select the `main` branch
6. Keep the main file as `app.py`
7. Click "Deploy"

## Step 4: Add Streamlit Secrets

After deployment, you need to add secrets:

1. In your Streamlit app dashboard, click "⋮" (three dots) → "Settings"
2. Go to "Secrets" tab
3. Add these secrets:

```toml
GEMINI_API_KEY = "your-gemini-api-key-here"
GOOGLE_SERVICE_ACCOUNT_JSON = '''{"type": "service_account", "project_id": "your-project-id", "private_key_id": "...", "private_key": "...", "client_email": "...", "client_id": "...", "auth_uri": "...", "token_uri": "...", "auth_provider_x509_cert_url": "...", "client_x509_cert_url": "..."}'''
```

4. Click "Save" and your app will restart with the secrets

## Required API Keys Setup

### Gemini API Key
1. Go to https://ai.google.dev/api-keys
2. Create a new API key
3. Copy the key for Streamlit secrets

### Google Service Account
1. Go to https://console.cloud.google.com/
2. Create a new project or select existing
3. Enable "Google Slides API" and "Google Drive API"
4. Go to "IAM & Admin" → "Service Accounts"
5. Create service account with:
   - Name: `streamlit-slides-access`
   - Role: `Editor` (or custom role with Slides/Drive permissions)
6. Create and download JSON key
7. Copy the entire JSON content for Streamlit secrets

## Final Testing

Once deployed, test your live app:
1. Paste a sample Upwork job posting
2. Enter your Gemini API key in the sidebar
3. Click "Analyze & Generate Proposal"
4. Download the generated PDF

Your app will be available at: `https://yourusername-upwork-proposal-agent.streamlit.app`
