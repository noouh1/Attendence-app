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

GMAIL_ADDRESS     = "noouhfff@gmail.com"   # ← your Gmail
GMAIL_APP_PASSWORD = "okniislvzproykaz"   # ← Gmail App Password

EVENT_NAME        = "IEEE Mega Event"               # ← event name (shown in email)
NAME_COLUMN       = "name"
EMAIL_COLUMN      = "email"

DELAY_SECONDS     = 1   # delay between emails (avoid spam filter)
# ─────────────────────────────────────────────────────────


def build_email_html(name, uid, event_name):
    """Returns modern styled HTML email body in English."""
    return f"""
    <html>
    <body style="margin:0; padding:0; background:#f5f7fa; font-family: 'Segoe UI', Arial, sans-serif;">
      
      <div style="max-width:520px; margin:40px auto; background:#ffffff; border-radius:16px;
                  box-shadow:0 8px 24px rgba(0,0,0,0.08); overflow:hidden;">
        
        <!-- Header -->
        <div style="background:linear-gradient(135deg, #4e73df, #224abe); padding:25px; text-align:center;">
          <h2 style="color:#ffffff; margin:0; font-size:22px;">🎟 Your Event Ticket</h2>
        </div>

        <!-- Body -->
        <div style="padding:30px;">
          
          <p style="font-size:16px; color:#333;">Dear <strong>{name}</strong>,</p>
          
          <p style="font-size:15px; color:#555; line-height:1.6;">
            We are pleased to invite you to attend <strong>{event_name}</strong>.
          </p>

          <p style="font-size:15px; color:#555;">
            Please present the following QR code at the entrance:
          </p>

          <!-- QR Code -->
          <div style="text-align:center; margin:25px 0;">
            <img src="cid:qrimage"
                 style="width:200px; height:200px; border-radius:12px;
                        border:1px solid #eee; padding:8px; background:#fafafa;" />
          </div>

          <!-- UID -->
          <div style="text-align:center; margin-top:10px;">
            <span style="font-size:13px; color:#888;">Registration ID:</span><br/>
            <code style="font-size:14px; color:#4e73df; background:#f1f3f9; padding:6px 10px;
                         border-radius:6px; display:inline-block; margin-top:5px;">
              {uid}
            </code>
          </div>

          <hr style="border:none; border-top:1px solid #eee; margin:30px 0;" />

          <!-- Footer -->
          <p style="font-size:12px; color:#aaa; text-align:center; line-height:1.5;">
            This is an automated message. Please do not reply.<br/>
            We look forward to seeing you at the event!
          </p>

        </div>
      </div>

    </body>
    </html>
    """


def send_email(smtp, to_email, name, uid, qr_path, event_name):
    msg = MIMEMultipart("related")
    msg["Subject"] = f"🎟 Your Event Ticket — {event_name}"
    msg["From"]    = GMAIL_ADDRESS
    msg["To"]      = to_email

    # Plain + HTML versions (consistent English tone)
    alt = MIMEMultipart("alternative")

    plain_text = f"""Dear {name},

You are invited to attend {event_name}.

Please present your QR code at the entrance.

Registration ID: {uid}

This is an automated message. Please do not reply.
"""

    alt.attach(MIMEText(plain_text, "plain", "utf-8"))
    alt.attach(MIMEText(build_email_html(name, uid, event_name), "html", "utf-8"))
    msg.attach(alt)

    # Attach QR image inline
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
