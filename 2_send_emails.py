"""
STEP 2 — Send Emails with QR Codes
====================================
- Reads people_with_ids.xlsx
- Sends each person a personalized email with their QR code attached

BEFORE RUNNING:
    1. Enable 2FA on your Gmail account
    2. Go to: Google Account → Security → App Passwords
    3. Create an App Password for "Mail"
    4. Paste it in GMAIL_APP_PASSWORD below

HOW TO RUN:
    python 2_send_emails.py
"""

import pandas as pd
import smtplib
import os
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text     import MIMEText
from email.mime.image    import MIMEImage

# ─── CONFIG ──────────────────────────────────────────────
EXCEL_FILE        = "people_with_ids.xlsx"
QR_FOLDER         = "qr_codes"

GMAIL_ADDRESS     = "your_email@gmail.com"   # ← your Gmail
GMAIL_APP_PASSWORD = "xxxx xxxx xxxx xxxx"   # ← Gmail App Password

EVENT_NAME        = "الفعالية"               # ← event name (shown in email)
NAME_COLUMN       = "name"
EMAIL_COLUMN      = "email"

DELAY_SECONDS     = 1   # delay between emails (avoid spam filter)
# ─────────────────────────────────────────────────────────


def build_email_html(name, uid, event_name):
    """Returns beautiful HTML email body."""
    return f"""
    <html><body style="font-family: Arial, sans-serif; direction: rtl; background:#f4f4f4; padding:20px;">
      <div style="max-width:500px; margin:auto; background:white; border-radius:12px;
                  padding:30px; box-shadow:0 2px 8px rgba(0,0,0,0.1);">
        <h2 style="color:#2c3e50; text-align:center;">🎫 تذكرة حضورك</h2>
        <p style="font-size:16px;">عزيزي/عزيزتي <strong>{name}</strong>،</p>
        <p>يسعدنا دعوتك لحضور <strong>{event_name}</strong>.</p>
        <p>الرجاء تقديم QR Code التالي عند الدخول:</p>
        <div style="text-align:center; margin:20px 0;">
          <img src="cid:qrimage" style="width:200px; height:200px; border:2px solid #eee; border-radius:8px;"/>
        </div>
        <p style="color:#888; font-size:13px; text-align:center;">رقم التسجيل: <code>{uid}</code></p>
        <hr style="border:none; border-top:1px solid #eee; margin:20px 0;"/>
        <p style="color:#aaa; font-size:12px; text-align:center;">هذه الرسالة تلقائية، يُرجى عدم الرد عليها.</p>
      </div>
    </body></html>
    """


def send_email(smtp, to_email, name, uid, qr_path, event_name):
    msg = MIMEMultipart("related")
    msg["Subject"] = f"🎫 QR Code الخاص بك — {event_name}"
    msg["From"]    = GMAIL_ADDRESS
    msg["To"]      = to_email

    # HTML body
    alt = MIMEMultipart("alternative")
    alt.attach(MIMEText(f"عزيزي {name}، QR Code الخاص بك: {uid}", "plain", "utf-8"))
    alt.attach(MIMEText(build_email_html(name, uid, event_name), "html", "utf-8"))
    msg.attach(alt)

    # Embed QR image inline
    with open(qr_path, "rb") as f:
        img = MIMEImage(f.read(), _subtype="png")
        img.add_header("Content-ID", "<qrimage>")
        img.add_header("Content-Disposition", "inline", filename="qr.png")
        msg.attach(img)

    smtp.send_message(msg)


def send_all_emails():
    df = pd.read_excel(EXCEL_FILE)
    total = len(df)

    print(f"📧 Connecting to Gmail...")
    sent = 0
    failed = []

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        print(f"   ✅ Connected. Sending {total} emails...\n")

        for i, row in df.iterrows():
            name  = str(row.get(NAME_COLUMN, ""))
            email = str(row.get(EMAIL_COLUMN, "")).strip()
            uid   = str(row["unique_id"])
            qr_path = f"{QR_FOLDER}/{uid}.png"

            if not email or "@" not in email:
                print(f"   ⚠️  [{i+1}/{total}] Skipped (no email): {name}")
                continue

            if not os.path.exists(qr_path):
                print(f"   ⚠️  [{i+1}/{total}] QR not found for: {uid}")
                continue

            try:
                send_email(smtp, email, name, uid, qr_path, EVENT_NAME)
                sent += 1
                print(f"   ✅ [{sent}/{total}] Sent → {name} ({email})")
                time.sleep(DELAY_SECONDS)
            except Exception as e:
                failed.append({"name": name, "email": email, "error": str(e)})
                print(f"   ❌ Failed → {name}: {e}")

    print(f"\n{'='*50}")
    print(f"✅ Sent: {sent} / {total}")
    if failed:
        print(f"❌ Failed: {len(failed)}")
        for f in failed:
            print(f"   - {f['name']} ({f['email']}): {f['error']}")
    print("="*50)


if __name__ == "__main__":
    send_all_emails()
