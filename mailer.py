import smtplib
import os
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

EMAIL_SENDER = os.environ.get("EMAIL_SENDER", "")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD", "")
SUBSCRIBERS_FILE = "subscribers.json"

def load_subscribers():
    if os.path.exists(SUBSCRIBERS_FILE):
        with open(SUBSCRIBERS_FILE, "r") as f:
            return json.load(f)
    return []

def save_subscribers(subscribers):
    with open(SUBSCRIBERS_FILE, "w") as f:
        json.dump(subscribers, f, indent=2)

def add_subscriber(email, schedule="both", topics=None):
    subscribers = load_subscribers()
    emails = [s["email"] for s in subscribers]
    if email in emails:
        return False, "Already subscribed"
    subscribers.append({
        "email": email,
        "schedule": schedule,
        "topics": topics or ["world", "tech", "business", "politics"],
        "joined": datetime.now().isoformat()
    })
    save_subscribers(subscribers)
    return True, "Subscribed successfully"

def remove_subscriber(email):
    subscribers = load_subscribers()
    subscribers = [s for s in subscribers if s["email"] != email]
    save_subscribers(subscribers)

def send_email(to_email, subject, html_body):
    if not EMAIL_SENDER or not EMAIL_PASSWORD:
        return False, "Email credentials not configured"
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"The Brief <{EMAIL_SENDER}>"
        msg["To"] = to_email
        msg.attach(MIMEText(html_body, "html"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, to_email, msg.as_string())
        return True, "Sent"
    except Exception as e:
        return False, str(e)

def build_email_html(articles_by_category, edition="Morning"):
    now = datetime.now().strftime("%B %d, %Y")
    html = f"""
    <html><body style="margin:0;padding:0;background:#f5f0e8;font-family:'Georgia',serif;">
    <div style="max-width:680px;margin:0 auto;background:#f5f0e8;">
        <div style="background:#1a1410;padding:32px;text-align:center;">
            <div style="font-size:36px;font-weight:900;color:#f5f0e8;letter-spacing:-1px;">The <span style="color:#c1440e">Brief</span></div>
            <div style="font-size:11px;letter-spacing:3px;color:#6b5d50;text-transform:uppercase;margin-top:6px;">{edition} Edition · {now}</div>
        </div>
        <div style="background:#c1440e;height:4px;"></div>
        <div style="padding:40px 40px 0;">
            <p style="font-size:16px;color:#5a4a3a;line-height:1.8;border-left:3px solid #c1440e;padding-left:16px;">
                Your {edition.lower()} intelligence brief — top stories across world news, technology, business and politics.
            </p>
        </div>
    """
    category_labels = {"world": "🌍 World News", "tech": "💻 Technology", "business": "📈 Business & Economy", "politics": "🏛 Politics"}
    for category, articles in articles_by_category.items():
        if not articles:
            continue
        label = category_labels.get(category, category.title())
        html += f"""
        <div style="padding:32px 40px 0;">
            <div style="font-size:11px;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:#c1440e;border-bottom:2px solid #c1440e;padding-bottom:8px;margin-bottom:20px;">{label}</div>
        """
        for a in articles[:4]:
            title = a.get("title", "")
            source = a.get("source", "")
            url = a.get("url", "")
            desc = a.get("description", "")
            date = a.get("publishedAt", "")
            html += f"""
            <div style="margin-bottom:20px;padding-bottom:20px;border-bottom:1px solid #e0d8cc;">
                <div style="font-size:11px;color:#c1440e;font-weight:700;letter-spacing:1px;text-transform:uppercase;margin-bottom:6px;">{source} · {date}</div>
                <a href="{url}" style="font-size:17px;font-weight:700;color:#1a1410;text-decoration:none;line-height:1.4;display:block;margin-bottom:6px;">{title}</a>
                <div style="font-size:14px;color:#5a4a3a;line-height:1.6;">{desc[:200]}...</div>
            </div>
            """
        html += "</div>"
    html += f"""
        <div style="padding:32px 40px;text-align:center;margin-top:32px;border-top:1px solid #d9d0c4;">
            <div style="font-size:11px;color:#c9bfb0;letter-spacing:1px;">
                You're receiving this because you subscribed to The Brief.
            </div>
        </div>
    </div></body></html>
    """
    return html

def send_brief_to_all(edition="Morning"):
    from digest import fetch_category
    subscribers = load_subscribers()
    if not subscribers:
        return 0
    articles_by_category = {
        "world": fetch_category("world"),
        "tech": fetch_category("tech"),
        "business": fetch_category("business"),
        "politics": fetch_category("politics"),
    }
    html = build_email_html(articles_by_category, edition)
    subject = f"The Brief — {edition} Edition · {datetime.now().strftime('%B %d')}"
    sent = 0
    for sub in subscribers:
        success, _ = send_email(sub["email"], subject, html)
        if success:
            sent += 1
    return sent
    