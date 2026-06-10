import os
import smtplib
import ssl
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv

load_dotenv()

SOURCE_COLORS = {
    "greenhouse": "#00a862",
    "lever": "#5833b5",
    "ashby": "#ff6b35",
    "scraped": "#2563eb",
}


def _jobs_html(jobs: list[dict]) -> str:
    rows = ""
    for job in jobs:
        source = job.get("source", "scraped")
        color = SOURCE_COLORS.get(source, "#666")
        apply_url = job.get("url", "#") or "#"
        title = job.get("title", "Unknown Position")

        rows += f"""
        <tr>
          <td style="padding:12px 16px;border-bottom:1px solid #e5e7eb;">
            <strong style="font-size:14px;color:#111827;">{title}</strong>
          </td>
          <td style="padding:12px 16px;border-bottom:1px solid #e5e7eb;text-align:center;">
            <span style="background:{color};color:#fff;padding:3px 10px;border-radius:12px;font-size:11px;text-transform:capitalize;font-weight:600;">{source}</span>
          </td>
          <td style="padding:12px 16px;border-bottom:1px solid #e5e7eb;text-align:center;">
            <a href="{apply_url}" style="background:#2563eb;color:#fff;padding:6px 14px;border-radius:6px;text-decoration:none;font-size:12px;font-weight:600;">Apply →</a>
          </td>
        </tr>"""

    return f"""
    <table style="width:100%;border-collapse:collapse;background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,.08);">
      <thead>
        <tr style="background:#f9fafb;">
          <th style="padding:10px 16px;text-align:left;font-size:11px;color:#6b7280;text-transform:uppercase;font-weight:600;">Title</th>
          <th style="padding:10px 16px;text-align:center;font-size:11px;color:#6b7280;text-transform:uppercase;font-weight:600;">Source</th>
          <th style="padding:10px 16px;text-align:center;font-size:11px;color:#6b7280;text-transform:uppercase;font-weight:600;">Apply</th>
        </tr>
      </thead>
      <tbody>{rows}</tbody>
    </table>"""


def _build_html(jobs_by_company: dict[str, list[dict]], date_str: str, timestamp: str) -> str:
    total = sum(len(v) for v in jobs_by_company.values())
    company_count = len(jobs_by_company)

    sections = ""
    for company_name, jobs in jobs_by_company.items():
        sections += f"""
        <div style="margin-bottom:32px;">
          <h2 style="font-size:17px;color:#111827;margin:0 0 12px;padding-bottom:8px;border-bottom:2px solid #2563eb;">
            {company_name}
          </h2>
          {_jobs_html(jobs)}
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
</head>
<body style="margin:0;padding:0;background:#f3f4f6;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
  <div style="max-width:620px;margin:40px auto;padding:0 16px;">

    <div style="background:linear-gradient(135deg,#1d4ed8,#7c3aed);border-radius:12px 12px 0 0;padding:32px;text-align:center;">
      <h1 style="color:#fff;margin:0;font-size:22px;font-weight:700;">🔍 Frontend Jobs Found</h1>
      <p style="color:rgba(255,255,255,.8);margin:6px 0 0;font-size:14px;">{date_str}</p>
    </div>

    <div style="background:#fff;padding:32px;border-radius:0 0 12px 12px;box-shadow:0 4px 20px rgba(0,0,0,.08);">

      <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:8px;padding:14px 20px;margin-bottom:32px;text-align:center;">
        <p style="margin:0;color:#1e40af;font-size:14px;">
          Found <strong>{total} frontend role(s)</strong> across <strong>{company_count} company/companies</strong>
        </p>
      </div>

      {sections}

      <div style="border-top:1px solid #e5e7eb;padding-top:20px;text-align:center;">
        <p style="margin:0;color:#9ca3af;font-size:12px;">Sent by your Job Scraper • {timestamp}</p>
      </div>
    </div>
  </div>
</body>
</html>"""


def send_email(jobs_data: list[dict]) -> None:
    sender = os.getenv("GMAIL_SENDER")
    password = os.getenv("GMAIL_APP_PASSWORD")
    receiver = os.getenv("GMAIL_RECEIVER", sender)

    if not sender or not password:
        raise ValueError("GMAIL_SENDER and GMAIL_APP_PASSWORD environment variables must be set")

    jobs_by_company: dict[str, list[dict]] = {}
    for job in jobs_data:
        company = job.get("company_name", "Unknown")
        jobs_by_company.setdefault(company, []).append(job)

    now = datetime.utcnow()
    date_str = now.strftime("%B %d, %Y")
    timestamp = now.strftime("%Y-%m-%d %H:%M UTC")
    count = len(jobs_data)

    subject = f"🔍 Frontend Jobs Found — {date_str} ({count} new)"
    html_body = _build_html(jobs_by_company, date_str, timestamp)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = receiver
    msg.attach(MIMEText(html_body, "html"))

    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ctx) as server:
        server.login(sender, password)
        server.sendmail(sender, receiver, msg.as_string())
