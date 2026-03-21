# Deploy Product Analytics Dashboard to Streamlit Cloud

Follow these steps to deploy your app so you can share a live link with your founders.

## Prerequisites

- A [GitHub](https://github.com) account
- A [Streamlit Community Cloud](https://share.streamlit.io) account (free, sign up with GitHub)

---

## Step 1: Create a GitHub repository

1. Go to [github.com/new](https://github.com/new)
2. **Repository name**: `product-analytics-dashboard` (or any name you like)
3. **Visibility**: Private or Public (Private is fine; Streamlit Cloud can access private repos)
4. Do **not** initialize with README (we're pushing existing files)
5. Click **Create repository**

---

## Step 2: Push your project to GitHub

Open Terminal and run:

```bash
cd "/Users/udhayaaaaaa/Documents/product analytics"

# Initialize git (if not already)
git init

# Add all files (Excel files, app.py, requirements.txt)
git add .
git commit -m "Initial commit: Product Analytics Dashboard"

# Add your GitHub repo as remote (replace YOUR_USERNAME and REPO_NAME with yours)
git remote add origin https://github.com/YOUR_USERNAME/product-analytics-dashboard.git

# Push to GitHub
git branch -M main
git push -u origin main
```

**Replace** `YOUR_USERNAME` with your GitHub username and `REPO_NAME` with your repo name.

---

## Step 3: Deploy on Streamlit Community Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with your GitHub account
3. Click **"New app"**
4. Fill in:
   - **Repository**: `YOUR_USERNAME/product-analytics-dashboard`
   - **Branch**: `main`
   - **Main file path**: `app.py`
   - **App URL** (optional): e.g. `product-analytics-dashboard`
5. Click **"Deploy!"**

The first deployment takes 2–5 minutes. When it finishes, you'll get a URL like:
`https://product-analytics-dashboard-xxxxx.streamlit.app`

Share this link with your founders.

---

## Step 4: Update the app later

After changing the code locally:

```bash
cd "/Users/udhayaaaaaa/Documents/product analytics"
git add .
git commit -m "Update dashboard"
git push
```

Streamlit Cloud will redeploy automatically.

---

## Troubleshooting

- **App crashes on load**: Check the logs in the Streamlit Cloud dashboard.
- **"File not found"**: Ensure both Excel files are committed and pushed to GitHub.
- **Slow first load**: The Excel files are ~9MB total; first load may take 30–60 seconds.
