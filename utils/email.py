from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import smtplib
from threading import Thread


def _send_gmail_thread(recipient, subject, body):
  """Sends an email directly through Gmail SMTP over Port 465 SSL."""
  gmail_user = (os.getenv("MAIL_USERNAME") or "").strip()
  gmail_pass = (os.getenv("MAIL_PASSWORD") or "").replace(" ", "").strip()

  if not gmail_user or not gmail_pass:
    print(
        "[GMAIL ERROR] MAIL_USERNAME or MAIL_PASSWORD missing in Render"
        " Environment Variables!",
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


def send_otp_email(recipient, otp):
  """Dispatches the verification OTP via Gmail."""
  subject = "AirBook - Email Verification OTP"
  body = f"""Hello,

Your AirBook verification OTP is: {otp}

This OTP is valid for 10 minutes.

If you did not create an AirBook account, you can safely ignore this email.

Regards,
AirBook Team
"""
  t = Thread(target=_send_gmail_thread, args=(recipient, subject, body))
  t.daemon = True
  t.start()
  return True


def send_reset_otp_email(recipient, otp):
  """Dispatches the password reset OTP via Gmail."""
  subject = "AirBook - Password Reset OTP"
  body = f"""Hello,

Your AirBook password reset OTP is: {otp}

This OTP is valid for 10 minutes.

Regards,
AirBook Team
"""
  t = Thread(target=_send_gmail_thread, args=(recipient, subject, body))
  t.daemon = True
  t.start()
  return True