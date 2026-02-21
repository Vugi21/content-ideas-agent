#!/usr/bin/env python3
"""
Content Ideas Agent - Generates satire/humor video ideas using Claude
Sends weekly idea list via Gmail
"""

import os
import sys
import json
import html
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
import anthropic


def validate_env_vars() -> dict:
    """
    Validate all required environment variables are present before doing anything.
    Returns dict of env vars or exits with error.
    """
    required = {
        "CLAUDE_API_KEY": os.getenv("CLAUDE_API_KEY"),
        "GMAIL_ADDRESS": os.getenv("GMAIL_ADDRESS"),
        "GMAIL_APP_PASSWORD": os.getenv("GMAIL_APP_PASSWORD"),
        "RECIPIENT_EMAIL": os.getenv("RECIPIENT_EMAIL"),
    }
    missing = [k for k, v in required.items() if not v]
    if missing:
        print(f"Missing required environment variables: {', '.join(missing)}")
        sys.exit(1)
    return required


def generate_video_ideas(client: anthropic.Anthropic, trending_topics: list[str]) -> dict:
    """
    Use Claude to generate video ideas based on trending topics.
    Raises on failure - no silent fallback sending garbage.
    """
    topics_str = "\n".join([f"- {topic}" for topic in trending_topics])

    prompt = f"""You are a creative content strategist specializing in satire, humor, and political commentary.

Generate exactly 15 video ideas for a creator who makes satirical, humorous content about politics, current events, pop culture, and everyday life.

TRENDING TOPICS THIS WEEK:
{topics_str}

For each idea, provide:
1. Title (catchy, hook-focused)
2. Hook (first 3 seconds - what grabs attention)
3. Content type (Political satire / Pop culture / Everyday reality / Current events)
4. Platform fit (TikTok/Shorts / YouTube / Both)
5. Timeless or Topical (will this age well?)
6. Brief description (2-3 sentences)

RESPOND WITH ONLY VALID JSON. NO MARKDOWN, NO COMMENTS, JUST JSON:
{{
  "ideas": [
    {{
      "id": 1,
      "title": "Example Title",
      "hook": "Example hook text",
      "type": "Political satire",
      "platform": "TikTok/Shorts",
      "timeless": true,
      "description": "Example description here."
    }},
    {{
      "id": 2,
      "title": "Second Idea Title",
      "hook": "Second hook",
      "type": "Pop culture",
      "platform": "Both",
      "timeless": false,
      "description": "Another description."
    }}
  ]
}}

Generate exactly 15 ideas. Make them specific, actionable, and funny. Prioritize angles that feel fresh and satirical."""

    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=4096,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    response_text = message.content[0].text

    # Extract JSON from response
    start_idx = response_text.find('{')
    end_idx = response_text.rfind('}') + 1
    if start_idx == -1 or end_idx == 0:
        raise ValueError(f"No JSON object found in Claude response. Response was: {response_text[:200]}")

    json_str = response_text[start_idx:end_idx]

    try:
        ideas_data = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON parse failed: {e}. Extracted string (first 300 chars): {json_str[:300]}")

    if "ideas" not in ideas_data or not isinstance(ideas_data["ideas"], list) or len(ideas_data["ideas"]) == 0:
        raise ValueError(f"Response JSON missing 'ideas' array or it is empty. Keys found: {list(ideas_data.keys())}")

    print(f"Generated {len(ideas_data['ideas'])} video ideas")
    return ideas_data


def format_ideas_email(ideas_data: dict, trending_topics: list[str]) -> tuple[str, str]:
    """
    Format ideas into HTML email body.
    Returns (subject, html_body).
    All dynamic content is html.escape()'d to prevent rendering breakage.
    """
    ideas = ideas_data.get("ideas", [])

    timeless = [i for i in ideas if i.get("timeless", False)]
    topical = [i for i in ideas if not i.get("timeless", False)]

    def idea_block(idea: dict) -> str:
        platform = html.escape(str(idea.get('platform', 'N/A')))
        idea_type = html.escape(str(idea.get('type', 'N/A')))
        idea_id = html.escape(str(idea.get('id', '?')))
        title = html.escape(str(idea.get('title', 'Untitled')))
        hook = html.escape(str(idea.get('hook', '')))
        description = html.escape(str(idea.get('description', '')))
        return f"""
            <div class="idea">
                <div class="idea-title">#{idea_id} - {title}</div>
                <div class="idea-meta">
                    <span class="meta-tag">{platform}</span>
                    <span class="meta-tag">{idea_type}</span>
                </div>
                <div class="idea-hook">"{hook}"</div>
                <div class="idea-desc">{description}</div>
            </div>
        """

    timeless_blocks = "\n".join(idea_block(i) for i in timeless)
    topical_blocks = "\n".join(idea_block(i) for i in topical)
    topics_display = html.escape(", ".join(trending_topics))
    date_str = html.escape(datetime.now().strftime('%A, %B %d, %Y'))

    html_body = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #1f1f1f; color: #fff; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        .header h1 {{ margin: 0 0 8px 0; }}
        .header p {{ margin: 4px 0; }}
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
        .tips {{ background-color: #f0f0f0; padding: 15px; border-radius: 4px; margin-top: 30px; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Weekly Content Ideas</h1>
        <p>Your AI-powered satire &amp; humor video ideas for this week</p>
        <p style="font-size: 12px; color: #ccc;">Generated: {date_str}</p>
    </div>

    <div class="trending">
        <div class="trending-title">Trending Topics This Week:</div>
        {topics_display}
    </div>

    <div class="section">
        <div class="section-title">Timeless Ideas (Evergreen Content)</div>
        <p style="color: #666; font-size: 12px;">These won't age. Post anytime.</p>
        {timeless_blocks if timeless_blocks else '<p style="color:#999;">None this week.</p>'}
    </div>

    <div class="section">
        <div class="section-title">Topical Ideas (Time-Sensitive)</div>
        <p style="color: #666; font-size: 12px;">These are hot right now. Post this week for algorithmic boost.</p>
        {topical_blocks if topical_blocks else '<p style="color:#999;">None this week.</p>'}
    </div>

    <div class="tips">
        <p><strong>Pro Tips:</strong></p>
        <ul>
            <li>Post topical ideas immediately for trending boost</li>
            <li>Mix timeless &amp; topical in your weekly content (3:2 ratio)</li>
            <li>Film multiple variations of the same idea</li>
            <li>Use the hooks as your video openers</li>
        </ul>
    </div>
</body>
</html>"""

    subject = f"Weekly Video Ideas - {datetime.now().strftime('%B %d, %Y')}"
    return subject, html_body


def send_email(gmail_address: str, gmail_app_password: str, recipient_email: str,
               subject: str, html_body: str) -> None:
    """
    Send email via Gmail SMTP.
    Subject is RFC 2047 encoded to handle any unicode safely.
    Uses send_message() which handles all encoding internally.
    Raises on failure so the caller can decide what to do.
    """
    msg = MIMEMultipart("alternative")
    # RFC 2047 encode the subject so non-ASCII survives SMTP transport
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"] = gmail_address
    msg["To"] = recipient_email

    # UTF-8 charset on the HTML part handles all unicode in the body
    msg.attach(MIMEText(html_body, "html", _charset="utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(gmail_address, gmail_app_password)
        # send_message() reads From/To from headers and handles encoding correctly
        server.send_message(msg)


def main():
    print("Content Ideas Agent Starting...")

    # Validate env vars FIRST, before initializing anything
    env = validate_env_vars()

    # Initialize client only after we know the key exists
    client = anthropic.Anthropic(api_key=env["CLAUDE_API_KEY"])

    trending_topics = [
        "Election season drama",
        "AI taking over jobs",
        "Dating app failures",
        "Corporate layoffs",
        "Influencer controversies",
        "Rent prices hitting records",
        "Social media algorithm changes"
    ]

    print(f"Generating ideas based on {len(trending_topics)} trending topics...")

    try:
        ideas_data = generate_video_ideas(client, trending_topics)
    except Exception as e:
        print(f"Failed to generate ideas: {e}")
        sys.exit(1)

    subject, html_body = format_ideas_email(ideas_data, trending_topics)

    print("Sending email...")
    try:
        send_email(
            env["GMAIL_ADDRESS"],
            env["GMAIL_APP_PASSWORD"],
            env["RECIPIENT_EMAIL"],
            subject,
            html_body
        )
        print(f"Email sent successfully to {env['RECIPIENT_EMAIL']}")
    except Exception as e:
        print(f"Failed to send email: {e}")
        sys.exit(1)

    print("Agent completed successfully.")


if __name__ == "__main__":
    main()
