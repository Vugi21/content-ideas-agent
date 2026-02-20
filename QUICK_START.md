# Quick Start Checklist ⚡

## Pre-Deployment (Do These Now)

- [ ] Have Claude API key ready? (from console.anthropic.com)
- [ ] Have Gmail app password? (from myaccount.google.com/apppasswords)
  - Should be 16 characters like: `abcd efgh ijkl mnop`
- [ ] GitHub account created? 
- [ ] Render account created? (render.com - can use GitHub login)

## Step 1: Create GitHub Repo

1. Go to github.com/new
2. Name it: `content-ideas-agent`
3. Select "Public" (easier for Render)
4. Click "Create repository"
5. Copy the HTTPS URL (looks like `https://github.com/YOUR_USERNAME/content-ideas-agent.git`)

## Step 2: Upload Files to GitHub

Option A (Via GitHub Web UI - Easiest):
1. Open your new GitHub repo
2. Click "Add file" → "Upload files"
3. Drag and drop ALL these files:
   - `content_ideas_agent.py`
   - `requirements.txt`
   - `render.yaml`
   - `.env.example`
   - `.gitignore`
   - `README.md`
4. Click "Commit changes"

Option B (Via Git Command Line):
```bash
git clone https://github.com/YOUR_USERNAME/content-ideas-agent.git
cd content-ideas-agent
# Copy all the files into this folder
git add .
git commit -m "Initial commit"
git push origin main
```

## Step 3: Deploy on Render

1. Go to render.com (login with GitHub)
2. Click "New +" → "Web Service"
3. Select your `content-ideas-agent` repo
4. Fill in:
   - **Name:** `content-ideas-agent`
   - **Environment:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python content_ideas_agent.py`
   - **Plan:** Free
5. Click "Create Web Service"
6. Wait for deployment (2-3 minutes)

## Step 4: Add Environment Variables in Render

1. In your Render service dashboard, go to **Environment**
2. Add 4 variables (scroll down to "Environment Variables"):
   ```
   CLAUDE_API_KEY = sk-...your-key...
   GMAIL_ADDRESS = vahmadov@gmail.com
   GMAIL_APP_PASSWORD = abcd efgh ijkl mnop
   RECIPIENT_EMAIL = vahmadov@gmail.com
   ```
3. Click "Save"
4. Render will re-deploy automatically

## Step 5: Test

1. Go to your Render service → Logs
2. You should see the agent running
3. Check your email (vahmadov@gmail.com) for the ideas!

## Step 6: Schedule Weekly Runs (Optional)

For now, the agent runs once when you deploy. To make it run automatically every week, add the GitHub Actions workflow (see README.md for details).

---

## Troubleshooting

**Email didn't arrive?**
- Check Render logs for errors
- Verify Gmail app password is correct (spaces matter)
- Make sure 2FA is enabled on Gmail

**Deployment failed?**
- Check Render logs
- Verify all 4 environment variables are set
- Make sure render.yaml is in the repo

**Ideas look weird?**
- That's Claude being creative! Edit the prompt in `content_ideas_agent.py` if needed

---

## You're Done! 🎉

Your agent will now generate video ideas. Next steps:
1. Review the ideas when they arrive
2. Pick 5-6 for the week
3. Film them with Kling AI (~$10)
4. Post to TikTok/YouTube
5. Watch your audience grow!

Questions? Check the full README.md for details.
