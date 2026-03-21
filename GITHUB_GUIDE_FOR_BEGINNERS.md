# Complete Step-by-Step Guide: Deploy Your Dashboard (Beginner-Friendly)

This guide assumes you're new to GitHub. Follow each step in order.

---

## Part 1: Create a GitHub Account

### Step 1.1: Sign up
1. Open your browser and go to **https://github.com**
2. Click the green **"Sign up"** button (top right)
3. Enter your **email address**
4. Create a **password** (at least 15 characters, or 8+ with a number and lowercase letter)
5. Choose a **username** (e.g. `udhayadesigner` — this will be in your profile URL)
6. Type **y** when asked if you want product updates (optional)
7. Click **"Verify your account"** and complete the puzzle/captcha
8. Check your email and enter the **verification code** GitHub sent you
9. Choose **"Free"** plan
10. Skip the survey questions (or answer if you like)
11. Click **"Complete setup"**

Your account is ready.

---

## Part 2: Install GitHub Desktop (Easiest Way — No Command Line)

### Step 2.1: Download and install
1. Go to **https://desktop.github.com**
2. Click **"Download for macOS"** (or Windows if you use Windows)
3. Open the downloaded file (e.g. `GitHubDesktop-x64-mac.zip`)
4. Drag **GitHub Desktop** into your **Applications** folder
5. Open **GitHub Desktop** from Applications
6. If macOS asks "Are you sure?", click **Open**
7. Click **"Sign in to GitHub.com"** and sign in with your new account (browser will open)

---

## Part 3: Add Your Project to GitHub

### Step 3.1: Add the folder to GitHub Desktop
1. In **GitHub Desktop**, go to **File → Add Local Repository**
2. Click **"Choose..."** and go to:  
   `Documents/product analytics`
3. If you see **"This directory does not appear to be a Git repository"**, click **"create a repository"**
4. A popup appears:
   - **Name**: `product-analytics-dashboard` (or any name)
   - **Local Path**: should already show your folder path — leave it
   - **Initialize with README**: leave **unchecked**
   - Click **"Create Repository"**

### Step 3.2: Commit your files
1. On the **left side**, you’ll see a list of files (app.py, Excel files, etc.)
2. At the **bottom left**, in the summary box, type: `Initial upload`
3. Click the blue **"Commit to main"** button

### Step 3.3: Publish to GitHub
1. Click **"Publish repository"** (top right, or in the main area)
2. **Name**: `product-analytics-dashboard`
3. **Description** (optional): `Product Analytics Dashboard for founders`
4. **Keep this code private**: check this if you don’t want it public; uncheck for public
5. Click **"Publish Repository"**

Your project is now on GitHub.

---

## Part 4: Deploy on Streamlit Cloud (Get Your Shareable Link)

### Step 4.1: Go to Streamlit
1. Open **https://share.streamlit.io**
2. Click **"Sign up"** or **"Get started"**
3. Choose **"Continue with GitHub"**
4. Sign in with your GitHub account if asked
5. If Streamlit asks for permissions, click **"Authorize"**

### Step 4.2: Create your app
1. Click **"New app"**
2. You’ll see a form:
   - **Repository**: Click the dropdown and select `YOUR_USERNAME/product-analytics-dashboard`
   - **Branch**: Leave as `main`
   - **Main file path**: Type `app.py`
   - **App URL** (optional): e.g. `product-analytics` — this becomes part of your link
3. Click **"Deploy!"**

### Step 4.3: Wait for deployment
1. A progress screen appears
2. Wait **2–5 minutes** (first time is slower)
3. When it’s done, you’ll see **"Your app is live!"**
4. Copy the URL (e.g. `https://product-analytics-xxxxx.streamlit.app`)

**That’s your shareable link.** Send it to your founders.

---

## Part 5: Updating Your App Later (When You Change Something)

1. Open **GitHub Desktop**
2. It should show your repo; if not, go to **File → Add Local Repository** and add the folder again
3. Make your changes to the files (e.g. in Cursor)
4. In GitHub Desktop, you’ll see the changed files on the left
5. In the summary box, type what you changed (e.g. `Updated charts`)
6. Click **"Commit to main"**
7. Click **"Push origin"** (top right)

Streamlit Cloud will automatically redeploy in a few minutes.

---

## Troubleshooting

### "I don't see my repository in Streamlit"
- Make sure you clicked **"Publish Repository"** in GitHub Desktop
- Wait 1–2 minutes and refresh the Streamlit page

### "App crashes" or "Something went wrong"
- In Streamlit Cloud, click your app → **"Manage app"** → **"Logs"** to see the error
- Often it’s a missing file — check that both Excel files are in the repo (visible in GitHub Desktop before you committed)

### "I can't find my folder"
- The folder path is: `Documents/product analytics`
- On Mac: Open Finder → **Documents** → **product analytics**

### "GitHub Desktop says I need to sign in"
- Go to **GitHub Desktop → Preferences → Accounts**
- Click **"Sign in"** and complete the login in the browser

---

## Quick Reference: What Each Thing Does

| Term | Meaning |
|------|---------|
| **GitHub** | Place to store your code online |
| **GitHub Desktop** | App that lets you upload and update code without typing commands |
| **Repository (repo)** | Your project folder stored on GitHub |
| **Commit** | Save a snapshot of your files |
| **Push** | Send your commits to GitHub |
| **Streamlit Cloud** | Hosts your app and gives you a link to share |
