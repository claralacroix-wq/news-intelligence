import smtplib
import os
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
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
        msg["From"] = "The Brief <" + EMAIL_SENDER + ">"
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
    category_labels = {
        "world": "World News",
        "tech": "Technology",
        "business": "Business & Economy",
        "politics": "Politics"
    }
    html = "<html><body style='margin:0;padding:0;background:#f5f0e8;font-family:Georgia,serif;'>"
    html += "<div style='max-width:680px;margin:0 auto;'>"
    html += "<div style='background:#1a1410;padding:32px;text-align:center;'>"
    html += "<div style='font-size:36px;font-weight:900;color:#f5f0e8;'>The Brief</div>"
    html += "<div style='font-size:11px;letter-spacing:3px;color:#6b5d50;text-transform:uppercase;margin-top:6px;'>" + edition + " Edition - " + now + "</div>"
    html += "</div>"
    html += "<div style='background:#c1440e;height:4px;'></div>"
    for category, articles in articles_by_category.items():
        if not articles:
            continue
        label = category_labels.get(category, category.title())
        html += "<div style='padding:32px 40px 0;'>"
        html += "<div style='font-size:11px;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:#c1440e;border-bottom:2px solid #c1440e;padding-bottom:8px;margin-bottom:20px;'>" + label + "</div>"
        for a in articles[:4]:
            title = a.get("title", "")
            source = a.get("source", "")
            url = a.get("url", "")
            desc = a.get("description", "")[:200]
            date = a.get("publishedAt", "")
            html += "<div style='margin-bottom:20px;padding-bottom:20px;border-bottom:1px solid #e0d8cc;'>"
            html += "<div style='font-size:11px;color:#c1440e;font-weight:700;margin-bottom:6px;'>" + source + " - " + date + "</div>"
            html += "<a href='" + url + "' style='font-size:17px;font-weight:700;color:#1a1410;text-decoration:none;display:block;margin-bottom:6px;'>" + title + "</a>"
            html += "<div style='font-size:14px;color:#5a4a3a;line-height:1.6;'>" + desc + "</div>"
            html += "</div>"
        html += "</div>"
    html += "<div style='padding:32px 40px;text-align:center;border-top:1px solid #d9d0c4;'>"
    html += "<div style='font-size:11px;color:#c9bfb0;'>You are receiving this because you subscribed to The Brief.</div>"
    html += "</div></div></body></html>"
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
    subject = "The Brief - " + edition + " Edition - " + datetime.now().strftime("%B %d")
    sent = 0
    for sub in subscribers:
        success, _ = send_email(sub["email"], subject, html)
        if success:
            sent += 1
    return sent
    