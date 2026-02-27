import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
from digest import fetch_full_digest, CATEGORY_LABELS

load_dotenv()

EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_RECIPIENT = os.getenv("EMAIL_RECIPIENT")
# Options: "morning", "evening", "both" — set in .env as EMAIL_SCHEDULE=both
EMAIL_SCHEDULE = os.getenv("EMAIL_SCHEDULE", "both")

def build_email_html(digest, period="morning"):
    greeting = "Good Morning" if period == "morning" else "Good Evening"
    from datetime import datetime
    today = datetime.now().strftime("%B %d, %Y")

    sections = ""
    for category, articles in digest.items():
        if not articles:
            continue
        label = CATEGORY_LABELS.get(category, category.title())
        items = ""
        for a in articles[:4]:
            source = a.get("source", "")
            title = a.get("title", "")
            url = a.get("url", "#")
            desc = a.get("description", "")[:120]
            items += f"""
            <tr>
              <td style="padding: 14px 0; border-bottom: 1px solid #e0d8cc;">
                <div style="font-size:10px; font-weight:700; letter-spacing:2px; color:#c1440e; text-transform:uppercase; margin-bottom:6px;">{source}</div>
                <div style="font-size:16px; font-weight:700; color:#1a1410; margin-bottom:6px;">
                  <a href="{url}" style="color:#1a1410; text-decoration:none;">{title}</a>
                </div>
                <div style="font-size:13px; color:#8a7a6a; line-height:1.6;">{desc}...</div>
              </td>
            </tr>"""

        sections += f"""
        <tr><td style="padding: 32px 0 8px;">
          <div style="font-size:11px; font-weight:700; letter-spacing:3px; color:#8a7a6a; text-transform:uppercase; border-bottom:2px solid #1a1410; padding-bottom:8px; margin-bottom:4px;">{label}</div>
        </td></tr>
        {items}"""

    html = f"""
    <!DOCTYPE html>
    <html>
    <body style="margin:0; padding:0; background:#f5f0e8; font-family: Georgia, serif;">
      <table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f0e8;">
        <tr><td align="center" style="padding: 40px 20px;">
          <table width="620" cellpadding="0" cellspacing="0" style="background:#f5f0e8;">
            <tr><td style="background:#1a1410; padding:28px 40px; text-align:center;">
              <div style="font-size:36px; font-weight:900; color:#f5f0e8; letter-spacing:-1px; font-family:Georgia,serif;">
                The <span style="color:#c1440e;">Brief</span>
              </div>
              <div style="font-size:11px; letter-spacing:3px; color:#6b5d50; text-transform:uppercase; margin-top:4px;">
                AI-Powered News Intelligence
              </div>
            </td></tr>
            <tr><td style="background:#c1440e; height:4px;"></td></tr>
            <tr><td style="padding:32px 40px 0;">
              <div style="font-size:13px; font-weight:700; letter-spacing:3px; color:#c1440e; text-transform:uppercase; margin-bottom:12px;">{today}</div>
              <div style="font-size:28px; font-weight:900; color:#1a1410; line-height:1.2; margin-bottom:16px;">{greeting} — Here is your daily intelligence brief.</div>
              <div style="font-size:16px; color:#8a7a6a; font-style:italic; line-height:1.7;">
                A curated selection of the most important stories from across the global press.
              </div>
            </td></tr>
            <tr><td style="padding: 0 40px 40px;">
              <table width="100%" cellpadding="0" cellspacing="0">
                {sections}
              </table>
            </td></tr>
            <tr><td style="background:#1a1410; padding:20px 40px; text-align:center;">
              <div style="font-size:11px; color:#4a3d32; letter-spacing:1px; text-transform:uppercase;">
                The Brief — AI News Intelligence
              </div>
            </td></tr>
          </table>
        </td></tr>
      </table>
    </body>
    </html>"""
    return html


def send_digest_email(period="morning"):
    if not EMAIL_SENDER or not EMAIL_PASSWORD or not EMAIL_RECIPIENT:
        print("Email credentials missing in .env")
        return False

    print(f"Fetching digest for {period} email...")
    digest = fetch_full_digest()
    html = build_email_html(digest, period)
    subject = "☀️ Your Morning Brief — The Brief" if period == "morning" else "🌙 Your Evening Brief — The Brief"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECIPIENT
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECIPIENT, msg.as_string())
        print(f"✅ {period.title()} email sent to {EMAIL_RECIPIENT}")
        return True
    except Exception as e:
        print(f"❌ Email failed: {e}")
        return False


def should_send_morning():
    return EMAIL_SCHEDULE in ("morning", "both")

def should_send_evening():
    return EMAIL_SCHEDULE in ("evening", "both")


if __name__ == "__main__":
    send_digest_email("morning")
    