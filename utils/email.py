import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from threading import Thread
import requests

try:
  import resend
except ImportError:
  resend = None


def is_mail_configured():
  """Returns True when the app has credentials to send OTP emails."""
  if os.getenv("RESEND_API_KEY") or os.getenv("BREVO_API_KEY"):
    return True
  gmail_user = (os.getenv("MAIL_USERNAME") or "").strip()
  gmail_pass = (os.getenv("MAIL_PASSWORD") or "").replace(" ", "").strip()
  return bool(gmail_user and gmail_pass)


def _send_email_thread(recipient, subject, body):
  """Sends an email via Resend/Brevo HTTP API (Port 443 - works on Render Free Tier)
  or falls back to Gmail SMTP (localhost).
  """
  resend_api_key = (os.getenv("RESEND_API_KEY") or "").strip()
  brevo_api_key = (os.getenv("BREVO_API_KEY") or "").strip()

  # 1. Resend HTTP API (Port 443 - Never blocked on Render)
  if resend_api_key:
    try:
      print(f"[RESEND] Sending email via Resend API to {recipient}...", flush=True)
      from_email = os.getenv("MAIL_DEFAULT_SENDER") or "AirBook <onboarding@resend.dev>"
      if resend:
        resend.api_key = resend_api_key
        resend.Emails.send({
            "from": from_email,
            "to": [recipient],
            "subject": subject,
            "text": body,
        })
      else:
        resp = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {resend_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "from": from_email,
                "to": [recipient],
                "subject": subject,
                "text": body,
            },
            timeout=15,
        )
        resp.raise_for_status()
      print(f"[RESEND SUCCESS] Email successfully sent to {recipient}!", flush=True)
      return
    except Exception as e:
      print(f"[RESEND ERROR] Failed to send via Resend API: {repr(e)}", flush=True)

  # 2. Brevo HTTP API (Port 443 - Never blocked on Render)
  if brevo_api_key:
    try:
      print(f"[BREVO] Sending email via Brevo API to {recipient}...", flush=True)
      sender_email = (
          os.getenv("MAIL_DEFAULT_SENDER")
          or os.getenv("MAIL_USERNAME")
          or "airbookofficial@gmail.com"
      )
      resp = requests.post(
          "https://api.brevo.com/v3/smtp/email",
          headers={
              "api-key": brevo_api_key,
              "Content-Type": "application/json",
              "accept": "application/json",
          },
          json={
              "sender": {"name": "AirBook", "email": sender_email},
              "to": [{"email": recipient}],
              "subject": subject,
              "textContent": body,
          },
          timeout=15,
      )
      resp.raise_for_status()
      print(f"[BREVO SUCCESS] Email successfully sent to {recipient}!", flush=True)
      return
    except Exception as e:
      print(f"[BREVO ERROR] Failed to send via Brevo API: {repr(e)}", flush=True)

  # 3. Gmail SMTP (Works on localhost; blocked on Render Free Tier)
  gmail_user = (os.getenv("MAIL_USERNAME") or "").strip()
  gmail_pass = (os.getenv("MAIL_PASSWORD") or "").replace(" ", "").strip()

  if not gmail_user or not gmail_pass:
    print(
        "[MAIL ERROR] No mail configuration found! Provide RESEND_API_KEY, BREVO_API_KEY, or Gmail SMTP credentials.",
        flush=True,
    )
    return

  msg = MIMEMultipart()
  msg["Subject"] = subject
  msg["From"] = f"AirBook <{gmail_user}>"
  msg["To"] = recipient
  msg.attach(MIMEText(body, "plain"))

  try:
    print(
        f"[GMAIL] Connecting to smtp.gmail.com:465 for {recipient}...",
        flush=True,
    )
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=20) as server:
      server.login(gmail_user, gmail_pass)
      server.sendmail(gmail_user, [recipient], msg.as_string())
    print(
        f"[GMAIL SUCCESS] Email successfully sent to {recipient}!",
        flush=True,
    )
  except Exception as e:
    print(
        f"[GMAIL ERROR] Failed to send via Gmail SMTP: {repr(e)}",
        flush=True,
    )


# Alias for backward compatibility
_send_gmail_thread = _send_email_thread


def send_otp_email(recipient, otp):
  """Dispatches the verification OTP."""
  subject = "AirBook - Email Verification OTP"
  body = f"""Hello,

Your AirBook verification OTP is: {otp}

This OTP is valid for 10 minutes.

If you did not create an AirBook account, you can safely ignore this email.

Regards,
AirBook Team
"""
  t = Thread(target=_send_email_thread, args=(recipient, subject, body))
  t.daemon = True
  t.start()
  return True


def send_reset_otp_email(recipient, otp):
  """Dispatches the password reset OTP."""
  subject = "AirBook - Password Reset OTP"
  body = f"""Hello,

Your AirBook password reset OTP is: {otp}

This OTP is valid for 10 minutes.

Regards,
AirBook Team
"""
  t = Thread(target=_send_email_thread, args=(recipient, subject, body))
  t.daemon = True
  t.start()
  return True