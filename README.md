# Content Ideas Agent 🚀

An AI-powered agent that generates satirical, humorous video ideas using Claude and sends them to your inbox weekly.

## What It Does

- **Generates 15 video ideas weekly** based on trending topics
- **Uses Claude AI** for creative ideation and satire
- **Automatically sends ideas via email** every week
- **Organizes by content type**: Political satire, pop culture, everyday reality, current events
- **Marks ideas as timeless or topical** so you know what to post now vs. later
- **Provides hooks and descriptions** ready to film

## Setup (5 minutes)

### Prerequisites
- Claude API key (from console.anthropic.com)
- Gmail account with app password (from myaccount.google.com/apppasswords)
- GitHub account
- Render account (free)

### Local Testing (Optional)

1. **Clone the repo:**
   ```bash
   git clone <your-repo-url>
   cd content-ideas-agent
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and add your actual values:
   # CLAUDE_API_KEY=sk-...
   # GMAIL_ADDRESS=your_email@gmail.com
   # GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
   # RECIPIENT_EMAIL=your_email@gmail.com
   ```

5. **Test locally:**
   ```bash
   python content_ideas_agent.py
   ```

## Deploy to Render (Free)

### Step 1: Push to GitHub

1. Create a new GitHub repository (name it `content-ideas-agent`)
2. Push this code to GitHub:
   ```bash
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/content-ideas-agent.git
   git push -u origin main
   ```

### Step 2: Deploy on Render

1. Go to **render.com** and sign up/login
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub account and select the `content-ideas-agent` repo
4. **Configure:**
   - **Name:** `content-ideas-agent`
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python content_ideas_agent.py`
   - **Plan:** Free

5. **Add Environment Variables** (in Render dashboard):
   - Click **"Environment"** in the left sidebar
   - Add these variables:
     - `CLAUDE_API_KEY` = your Claude API key
     - `GMAIL_ADDRESS` = your Gmail address
     - `GMAIL_APP_PASSWORD` = your 16-char app password
     - `RECIPIENT_EMAIL` = where ideas should be sent

6. Click **"Create Web Service"**
7. Render will deploy automatically

### Step 3: Schedule Weekly Runs

The current setup runs once when deployed. To make it run **every week**, you have two options:

#### Option A: Use Render Cron Jobs (Coming soon)
Monitor Render's cron job feature and enable it when available.

#### Option B: Use External Scheduler (GitHub Actions)
Create `.github/workflows/schedule.yml`:

```yaml
name: Weekly Ideas Generation

on:
  schedule:
    - cron: '0 9 * * 1'  # Every Monday at 9 AM UTC

jobs:
  generate-ideas:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run agent
        env:
          CLAUDE_API_KEY: ${{ secrets.CLAUDE_API_KEY }}
          GMAIL_ADDRESS: ${{ secrets.GMAIL_ADDRESS }}
          GMAIL_APP_PASSWORD: ${{ secrets.GMAIL_APP_PASSWORD }}
          RECIPIENT_EMAIL: ${{ secrets.RECIPIENT_EMAIL }}
        run: python content_ideas_agent.py
```

Then add your secrets to GitHub (Settings → Secrets and variables → Actions).

## How to Use

### First Time
1. Run locally with `python content_ideas_agent.py` to test
2. Check your email for the formatted ideas list
3. Once working, deploy to Render

### Weekly Workflow
1. **Agent sends ideas** to your email every week (once scheduled)
2. **Pick your 5-6 ideas** for the week
3. **Film them** using your video generator (Kling AI recommended)
4. **Post to TikTok/YouTube** following the platform recommendations

### Customizing Ideas

Edit the `trending_topics` list in `content_ideas_agent.py`:

```python
trending_topics = [
    "Topic 1",
    "Topic 2",
    # Add your own trending topics
]
```

Or modify the prompt to change the type of ideas generated.

## Email Output

You'll receive a beautifully formatted email with:
- **15 ideas** sorted by timeless vs topical
- **Hooks** for the first 3 seconds
- **Platform recommendations** (TikTok/Shorts vs YouTube)
- **Content type tags** (Political, Pop culture, etc.)
- **Full descriptions** ready to film

## Troubleshooting

### Email not sending?
- Check GMAIL_APP_PASSWORD is correct (16 characters, spaces removed)
- Verify GMAIL_ADDRESS has 2FA enabled
- Check Render logs for error messages

### Claude API errors?
- Verify CLAUDE_API_KEY is valid (starts with `sk-`)
- Check you have API credits available

### Ideas not generating?
- Check Render logs: `render.com` → your service → Logs
- Verify all environment variables are set

## Architecture

```
User (vahmadov@gmail.com)
    ↓
Render (runs weekly) 
    ↓
Claude API (generates ideas)
    ↓
Gmail SMTP (sends formatted email)
    ↓
Your Inbox
```

## Cost

- **Render:** Free (with limits)
- **Claude API:** ~$0.01-0.05 per run (heavily discounted for batch)
- **Gmail:** Free
- **Total:** <$1/month

## Future Enhancements

- [ ] Auto-fetch trending topics from Twitter/Reddit API
- [ ] Track which ideas perform best (feedback loop)
- [ ] Save ideas to Notion or Google Sheets
- [ ] Generate video scripts automatically
- [ ] Integration with YouTube/TikTok for direct scheduling

## Support

Check Render logs if something fails:
1. Go to render.com
2. Select your service
3. Click "Logs" tab
4. Look for error messages

## License

MIT
