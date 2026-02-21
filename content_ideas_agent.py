#!/usr/bin/env python3
"""
content_ideas_agent.py

Weekly Content Ideas Agent (YouTube-first)
- Fetches trending topics from public RSS feeds (no API keys)
- Uses Claude to generate 10–15 satire/humor video ideas
- Organizes ideas by urgency (Topical vs Timeless) and platform fit
- Emails you a clean ASCII-only digest (no emojis, no special chars)

ENV VARS REQUIRED:
- CLAUDE_API_KEY
- GMAIL_ADDRESS
- GMAIL_APP_PASSWORD   (Google App Password)
- RECIPIENT_EMAIL

OPTIONAL:
- ANTHROPIC_MODEL      (default: claude-3-5-sonnet-latest)
- TOPICS_LIMIT         (default: 10)
- IDEAS_COUNT          (default: 15)
"""

import os
import re
import json
import smtplib
import unicodedata
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple

import requests
import anthropic
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


# ----------------------------
# Config
# ----------------------------
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest")
TOPICS_LIMIT = int(os.getenv("TOPICS_LIMIT", "10"))
IDEAS_COUNT = int(os.getenv("IDEAS_COUNT", "15"))

GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")

client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)


# ----------------------------
# Utilities: make everything ASCII (bulletproof vs codec errors)
# ----------------------------
def force_ascii(s: str) -> str:
    if s is None:
        return ""
    s = unicodedata.normalize("NFKD", s)
    s = s.replace("\u00a0", " ")  # NBSP
    s = s.encode("ascii", "ignore").decode("ascii")
    s = s.replace("\r\n", "\n")
    s = re.sub(r"[ \t]+", " ", s)
    return s.strip()


def safe_get_env() -> bool:
    missing = []
    for k in ["CLAUDE_API_KEY", "GMAIL_ADDRESS", "GMAIL_APP_PASSWORD", "RECIPIENT_EMAIL"]:
        if not os.getenv(k):
            missing.append(k)
    if missing:
        print("Missing required environment variables: " + ", ".join(missing))
        return False
    return True


# ----------------------------
# Trending topics (no keys): RSS scraping
# ----------------------------
def fetch_rss_titles(url: str, limit: int = 10, timeout: int = 12) -> List[str]:
    """
    Pull titles from an RSS feed without extra dependencies.
    Minimal parsing by regex; good enough for titles.
    """
    try:
        resp = requests.get(url, timeout=timeout, headers={"User-Agent": "content-ideas-agent/1.0"})
        resp.raise_for_status()
        xml = resp.text
        titles = re.findall(r"<title><!\[CDATA\[(.*?)\]\]></title>|<title>(.*?)</title>", xml, re.IGNORECASE)
        out = []
        for a, b in titles:
            t = a or b
            t = re.sub(r"<[^>]+>", "", t)
            t = force_ascii(t)
            if not t:
                continue
            out.append(t)
        # First title is often feed name; drop it
        if out:
            out = out[1:]
        dedup = []
        seen = set()
        for t in out:
            key = t.lower()
            if key not in seen:
                seen.add(key)
                dedup.append(t)
            if len(dedup) >= limit:
                break
        return dedup
    except Exception as e:
        print(f"RSS fetch failed: {url} :: {e}")
        return []


def fetch_trending_topics(limit: int = 10) -> List[str]:
    """
    Aggregate a small, diverse set of "trend-like" topics:
    - Google News (Top stories)
    - Google News (Technology)
    - Google News (Business)
    This is not "TikTok trends" or "Twitter trends" (those require APIs),
    but it's reliable, free, and stable for a weekly ideation agent.
    """
    feeds = [
        "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=en-US&gl=US&ceid=US:en",
    ]

    topics: List[str] = []
    for url in feeds:
        topics.extend(fetch_rss_titles(url, limit=limit))

    # Dedup + clamp
    final = []
    seen = set()
    for t in topics:
        key = t.lower()
        if key not in seen:
            seen.add(key)
            final.append(t)
        if len(final) >= limit:
            break

    # Fallback if RSS is blocked
    if not final:
        final = [
            "Election season drama",
            "AI taking over jobs",
            "Dating app failures",
            "Corporate layoffs",
            "Influencer controversies",
            "Rent prices hitting records",
            "Social media algorithm changes",
        ][:limit]

    return final


# ----------------------------
# Claude generation
# ----------------------------
def build_prompt(trending_topics: List[str], ideas_count: int) -> str:
    topics_str = "\n".join([f"- {t}" for t in trending_topics])

    # Tight constraints = less garbage output.
    # YouTube-first, but still includes Shorts.
    return f"""
You are a YouTube-first content strategist specializing in satire and humor.

Task:
Generate exactly {ideas_count} video ideas based on the trending topics below.

Constraints:
- Make ideas specific, actionable, and funny (satire/humor).
- Avoid vague advice. Each idea should be filmable in 30-120 seconds.
- Prioritize YouTube (long form) but include Shorts fit where relevant.
- Provide strong hooks and 3 talking points per idea.
- Output MUST be valid JSON only.

TRENDING TOPICS:
{topics_str}

Return JSON in this schema exactly:
{{
  "ideas": [
    {{
      "id": 1,
      "title": "Short, clickable title",
      "hook": "First 3 seconds line",
      "platform": "YouTube" | "Shorts" | "Both",
      "urgency": "Topical" | "Timeless",
      "angle": "What makes this take fresh",
      "talking_points": ["Point 1", "Point 2", "Point 3"]
    }}
  ]
}}

Rules:
- Exactly {ideas_count} items in ideas.
- talking_points must have exactly 3 items.
""".strip()


def extract_json(text: str) -> Dict[str, Any]:
    start = text.find("{")
    end = text.rfind("}") + 1
    if start == -1 or end <= 0:
        raise ValueError("No JSON object found")
    return json.loads(text[start:end])


def generate_video_ideas(trending_topics: List[str], ideas_count: int) -> Dict[str, Any]:
    prompt = build_prompt(trending_topics, ideas_count)

    msg = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = msg.content[0].text
    # Make parsing more robust
    try:
        data = extract_json(raw)
        ideas = data.get("ideas", [])
        if not isinstance(ideas, list) or len(ideas) == 0:
            raise ValueError("Missing ideas array")
        return data
    except Exception as e:
        print(f"JSON parse failed: {e}. Using fallback ideas.")
        # Fallback that still matches schema
        fallback = []
        for i in range(1, min(ideas_count, 10) + 1):
            fallback.append(
                {
                    "id": i,
                    "title": f"Satire Idea {i}",
                    "hook": "Here is the ridiculous part nobody is saying out loud...",
                    "platform": "Both",
                    "urgency": "Topical" if i % 2 == 0 else "Timeless",
                    "angle": "Deadpan serious delivery about an obviously absurd situation.",
                    "talking_points": [
                        "What happened (one sentence).",
                        "Why its absurd (one sentence).",
                        "Your punchline take (one sentence).",
                    ],
                }
            )
        return {"ideas": fallback}


# ----------------------------
# Email formatting (plain text, ASCII-only)
# ----------------------------
def format_email(ideas_data: Dict[str, Any], trending_topics: List[str]) -> Tuple[str, str]:
    ideas = ideas_data.get("ideas", [])

    topical = [i for i in ideas if i.get("urgency") == "Topical"]
    timeless = [i for i in ideas if i.get("urgency") == "Timeless"]

    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    subject = f"Weekly Video Ideas - {datetime.now().strftime('%B %d, %Y')}"
    subject = force_ascii(subject)

    lines = []
    lines.append("WEEKLY VIDEO IDEAS (YouTube-first)")
    lines.append(f"Generated: {now_str}")
    lines.append("")
    lines.append("TRENDING INPUTS:")
    for t in trending_topics:
        lines.append(f"- {force_ascii(t)}")
    lines.append("")
    lines.append("RATIONALE (how to use this):")
    lines.append("- Topical: publish this week for relevance.")
    lines.append("- Timeless: batch record and drip feed over time.")
    lines.append("- Each idea includes: hook + fresh angle + 3 talking points.")
    lines.append("")

    def render_section(title: str, items: List[Dict[str, Any]]) -> None:
        lines.append("=" * 60)
        lines.append(title.upper())
        lines.append("=" * 60)
        if not items:
            lines.append("(none)")
            lines.append("")
            return
        for it in items:
            _id = it.get("id", "?")
            lines.append(f"{_id}. {force_ascii(it.get('title', 'Untitled'))}")
            lines.append(f"   Platform: {force_ascii(it.get('platform', 'N/A'))} | Urgency: {force_ascii(it.get('urgency', 'N/A'))}")
            lines.append(f"   Hook: {force_ascii(it.get('hook', ''))}")
            lines.append(f"   Angle: {force_ascii(it.get('angle', ''))}")
            tps = it.get("talking_points", [])
            if isinstance(tps, list):
                for idx, tp in enumerate(tps[:3], start=1):
                    lines.append(f"   TP{idx}: {force_ascii(str(tp))}")
            lines.append("")

    render_section("Topical ideas (post this week)", topical)
    render_section("Timeless ideas (evergreen)", timeless)

    body = "\n".join(lines)
    body = force_ascii(body)
    return subject, body


def send_email(subject: str, body: str) -> bool:
    try:
        subject = force_ascii(subject)
        body = force_ascii(body)

        msg = MIMEMultipart()
        msg["Subject"] = subject
        msg["From"] = GMAIL_ADDRESS
        msg["To"] = RECIPIENT_EMAIL

        # ASCII only to prevent any codec issues
        msg.attach(MIMEText(body, "plain", _charset="us-ascii"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.send_message(msg)

        print(f"Email sent to {RECIPIENT_EMAIL}")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False


# ----------------------------
# Main
# ----------------------------
def main():
    print("Content Ideas Agent starting...")

    if not safe_get_env():
        return

    print("Fetching trending topics...")
    trending = fetch_trending_topics(limit=TOPICS_LIMIT)
    print(f"Trending topics loaded: {len(trending)}")

    print("Generating ideas via Claude...")
    ideas_data = generate_video_ideas(trending, ideas_count=IDEAS_COUNT)
    ideas_count = len(ideas_data.get("ideas", []))
    print(f"Ideas generated: {ideas_count}")

    subject, body = format_email(ideas_data, trending)

    print("Sending email...")
    ok = send_email(subject, body)

    if ok:
        print("Done.")
    else:
        print("Done (email failed).")


if __name__ == "__main__":
    main()
