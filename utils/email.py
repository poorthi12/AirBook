import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def is_mail_configured():
  """Returns True when the app has credentials to send OTP emails via SMTP."""
  smtp_user = (os.getenv("MAIL_USERNAME") or "").strip()
  smtp_pass = (os.getenv("MAIL_PASSWORD") or "").replace(" ", "").strip()
  return bool(smtp_user and smtp_pass)


def _send_email_thread(recipient, subject, body):
  """Sends an email via SMTP (supports Gmail, Outlook, and any standard SMTP server)."""
  smtp_server = (os.getenv("MAIL_SERVER") or "smtp.gmail.com").strip()
  smtp_port = int(os.getenv("MAIL_PORT") or 587)
  use_tls = os.getenv("MAIL_USE_TLS", "True").strip().lower() in ("1", "true", "yes")
  smtp_user = (os.getenv("MAIL_USERNAME") or "").strip()
  smtp_pass = (os.getenv("MAIL_PASSWORD") or "").replace(" ", "").strip()
  sender_name = os.getenv("MAIL_DEFAULT_SENDER") or f"AirBook <{smtp_user}>"

  if not smtp_user or not smtp_pass:
    print(
        "[MAIL ERROR] No SMTP credentials found! Set MAIL_USERNAME and MAIL_PASSWORD in your environment.",
        flush=True,
    )
    return False

  msg = MIMEMultipart()
  msg["Subject"] = subject
  msg["From"] = sender_name
  msg["To"] = recipient
  msg.attach(MIMEText(body, "plain"))

  try:
    print(
        f"[SMTP] Connecting to {smtp_server}:{smtp_port} for {recipient}...",
        flush=True,
    )
    if use_tls:
      with smtplib.SMTP(smtp_server, smtp_port, timeout=20) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, [recipient], msg.as_string())
    else:
      with smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=20) as server:
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, [recipient], msg.as_string())
    print(
        f"[SMTP SUCCESS] Email successfully sent to {recipient}!",
        flush=True,
    )
    return True
  except Exception as e:
    print(
        f"[SMTP ERROR] Failed to send email: {repr(e)}",
        flush=True,
    )
    return False


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
  return _send_email_thread(recipient, subject, body)


def send_reset_otp_email(recipient, otp):
  """Dispatches the password reset OTP."""
  subject = "AirBook - Password Reset OTP"
  body = f"""Hello,

Your AirBook password reset OTP is: {otp}

This OTP is valid for 10 minutes.

Regards,
AirBook Team
"""
  return _send_email_thread(recipient, subject, body)