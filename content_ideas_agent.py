#!/usr/bin/env python3
"""
Content Ideas Agent - Generates satire/humor video ideas using Claude
Sends weekly idea list via Gmail
"""

import os
import json
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import anthropic

# Initialize Anthropic client
client = anthropic.Anthropic(api_key=os.getenv("CLAUDE_API_KEY"))

# Gmail configuration from environment variables
GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")


def generate_video_ideas(trending_topics: list[str]) -> dict:
    """
    Use Claude to generate video ideas based on trending topics
    """
    
    topics_str = "\n".join([f"- {topic}" for topic in trending_topics])
    
    prompt = f"""You are a creative content strategist specializing in satire, humor, and political commentary.

Generate 15 video ideas for a creator who makes satirical, humorous content about politics, current events, pop culture, and everyday life.

TRENDING TOPICS THIS WEEK:
{topics_str}

For each idea, provide:
1. Title (catchy, hook-focused)
2. Hook (first 3 seconds - what grabs attention)
3. Content type (Political satire / Pop culture / Everyday reality / Current events)
4. Platform fit (TikTok/Shorts / YouTube / Both)
5. Timeless or Topical (will this age well?)
6. Brief description (2-3 sentences)

FORMAT YOUR RESPONSE AS JSON with this structure:
{{
  "ideas": [
    {{
      "id": 1,
      "title": "...",
      "hook": "...",
      "type": "...",
      "platform": "...",
      "timeless": true/false,
      "description": "..."
    }}
  ]
}}

Make the ideas specific, actionable, and funny. Prioritize angles that feel fresh and satirical, not surface-level observations."""

    message = client.messages.create(
        model="claude-opus-4-5-20251101",
        max_tokens=2000,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    # Parse response
    response_text = message.content[0].text
    
    # Extract JSON from response
    try:
        # Look for JSON in the response
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}') + 1
        json_str = response_text[start_idx:end_idx]
        ideas_data = json.loads(json_str)
    except (json.JSONDecodeError, ValueError):
        # Fallback if JSON parsing fails
        ideas_data = {"ideas": [{"error": "Failed to parse ideas"}]}
    
    return ideas_data


def format_ideas_email(ideas_data: dict, trending_topics: list[str]) -> tuple[str, str]:
    """
    Format ideas into a nice email body
    Returns (subject, html_body)
    """
    
    ideas = ideas_data.get("ideas", [])
    
    # Sort by timeless vs topical
    timeless = [i for i in ideas if i.get("timeless", False)]
    topical = [i for i in ideas if not i.get("timeless", False)]
    
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; color: #333; }}
            .header {{ background-color: #1f1f1f; color: #fff; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
            .section {{ margin-bottom: 30px; }}
            .section-title {{ font-size: 18px; font-weight: bold; color: #1f1f1f; border-bottom: 2px solid #007bff; padding-bottom: 10px; margin-bottom: 15px; }}
            .idea {{ background-color: #f8f9fa; padding: 15px; margin-bottom: 15px; border-left: 4px solid #007bff; border-radius: 4px; }}
            .idea-title {{ font-size: 16px; font-weight: bold; color: #007bff; margin-bottom: 8px; }}
            .idea-meta {{ font-size: 12px; color: #666; margin-bottom: 8px; }}
            .meta-tag {{ display: inline-block; background-color: #e9ecef; padding: 2px 8px; border-radius: 3px; margin-right: 8px; }}
            .idea-hook {{ font-style: italic; color: #555; margin-bottom: 8px; }}
            .idea-desc {{ color: #333; }}
            .trending {{ background-color: #fff3cd; padding: 15px; border-radius: 4px; margin-bottom: 20px; border-left: 4px solid #ffc107; }}
            .trending-title {{ font-weight: bold; margin-bottom: 10px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📹 Weekly Content Ideas</h1>
            <p>Your AI-powered satire & humor video ideas for this week</p>
            <p style="font-size: 12px; color: #ccc;">Generated: {datetime.now().strftime('%A, %B %d, %Y')}</p>
        </div>
        
        <div class="trending">
            <div class="trending-title">📊 Trending Topics This Week:</div>
            {', '.join(trending_topics)}
        </div>
        
        <div class="section">
            <div class="section-title">⏰ Timeless Ideas (Evergreen Content)</div>
            <p style="color: #666; font-size: 12px;">These won't age. Post anytime.</p>
    """
    
    for idea in timeless:
        platform_badge = f"<span class='meta-tag'>{idea.get('platform', 'N/A')}</span>"
        type_badge = f"<span class='meta-tag'>{idea.get('type', 'N/A')}</span>"
        
        html += f"""
            <div class="idea">
                <div class="idea-title">#{idea.get('id', '?')} - {idea.get('title', 'Untitled')}</div>
                <div class="idea-meta">{platform_badge} {type_badge}</div>
                <div class="idea-hook">"{idea.get('hook', '')}"</div>
                <div class="idea-desc">{idea.get('description', '')}</div>
            </div>
        """
    
    html += """
        </div>
        
        <div class="section">
            <div class="section-title">⚡ Topical Ideas (Time-Sensitive)</div>
            <p style="color: #666; font-size: 12px;">These are hot right now. Post this week for algorithmic boost.</p>
    """
    
    for idea in topical:
        platform_badge = f"<span class='meta-tag'>{idea.get('platform', 'N/A')}</span>"
        type_badge = f"<span class='meta-tag'>{idea.get('type', 'N/A')}</span>"
        
        html += f"""
            <div class="idea">
                <div class="idea-title">#{idea.get('id', '?')} - {idea.get('title', 'Untitled')}</div>
                <div class="idea-meta">{platform_badge} {type_badge}</div>
                <div class="idea-hook">"{idea.get('hook', '')}"</div>
                <div class="idea-desc">{idea.get('description', '')}</div>
            </div>
        """
    
    html += """
        </div>
        
        <div style="background-color: #f0f0f0; padding: 15px; border-radius: 4px; margin-top: 30px; font-size: 12px; color: #666;">
            <p><strong>💡 Pro Tips:</strong></p>
            <ul>
                <li>Post topical ideas immediately for trending boost</li>
                <li>Mix timeless & topical in your weekly content (3:2 ratio)</li>
                <li>Film multiple variations of the same idea</li>
                <li>Use the hooks as your video openers</li>
            </ul>
        </div>
    </body>
    </html>
    """
    
    subject = f"📹 Weekly Video Ideas - {datetime.now().strftime('%B %d, %Y')}"
    
    return subject, html


def send_email(subject: str, html_body: str):
    """
    Send email via Gmail SMTP
    """
    try:
        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = GMAIL_ADDRESS
        msg["To"] = RECIPIENT_EMAIL
        
        # Attach HTML
        msg.attach(MIMEText(html_body, "html"))
        
        # Send via Gmail SMTP
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_ADDRESS, RECIPIENT_EMAIL, msg.as_string())
        
        print(f"✅ Email sent successfully to {RECIPIENT_EMAIL}")
        return True
    except Exception as e:
        print(f"❌ Failed to send email: {str(e)}")
        return False


def main():
    """
    Main agent execution
    """
    print("🚀 Content Ideas Agent Starting...")
    
    # Check environment variables
    if not all([CLAUDE_API_KEY := os.getenv("CLAUDE_API_KEY"),
                GMAIL_ADDRESS,
                GMAIL_APP_PASSWORD,
                RECIPIENT_EMAIL]):
        print("❌ Missing required environment variables!")
        print("Required: CLAUDE_API_KEY, GMAIL_ADDRESS, GMAIL_APP_PASSWORD, RECIPIENT_EMAIL")
        return
    
    # Default trending topics (user can modify or we can fetch from an API later)
    trending_topics = [
        "Election season drama",
        "AI taking over jobs",
        "Dating app failures",
        "Corporate layoffs",
        "Influencer controversies",
        "Rent prices hitting records",
        "Social media algorithm changes"
    ]
    
    print(f"📊 Generating ideas based on {len(trending_topics)} trending topics...")
    
    # Generate ideas using Claude
    ideas_data = generate_video_ideas(trending_topics)
    
    print(f"✨ Generated {len(ideas_data.get('ideas', []))} video ideas")
    
    # Format email
    subject, html_body = format_ideas_email(ideas_data, trending_topics)
    
    # Send email
    print("📧 Sending email...")
    send_email(subject, html_body)
    
    print("✅ Agent completed successfully!")


if __name__ == "__main__":
    main()
