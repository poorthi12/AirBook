from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import smtplib
import socket
from threading import Thread
import traceback

# Force IPv4 so Render Linux does not hang on IPv6 blackholes
_orig_getaddrinfo = socket.getaddrinfo


def _getaddrinfo_ipv4(host, port, family=0, type=0, proto=0, flags=0):
  if host and "gmail.com" in str(host).lower():
    family = socket.AF_INET
  return _orig_getaddrinfo(host, port, family, type, proto, flags)


socket.getaddrinfo = _getaddrinfo_ipv4


def _send_smtp_email(recipient, subject, body):
  """Sends an email using standard Python smtplib with direct SSL."""
  mail_user = (os.getenv("MAIL_USERNAME") or "").strip()
  mail_pass = (os.getenv("MAIL_PASSWORD") or "").replace(" ", "").strip()
  mail_server = os.getenv("MAIL_SERVER", "smtp.gmail.com")
  mail_port = int(os.getenv("MAIL_PORT", 465))

  if not mail_user or not mail_pass:
    print(
        "[EMAIL WARNING] MAIL_USERNAME or MAIL_PASSWORD missing in"
        " environment variables.",
        flush=True,
    )
    return False

  msg = MIMEMultipart("alternative")
  msg["Subject"] = subject
  msg["From"] = f"AirBook <{mail_user}>"
  msg["To"] = recipient
  msg.attach(MIMEText(body, "plain"))

  try:
    with smtplib.SMTP_SSL(mail_server, mail_port, timeout=15) as server:
      server.login(mail_user, mail_pass)
      server.sendmail(mail_user, [recipient], msg.as_string())
    print(f"[EMAIL SUCCESS] Email delivered to {recipient}", flush=True)
    return True
  except Exception as e:
    print(
        f"[EMAIL ERROR] Failed to send email to {recipient}: {repr(e)}",
        flush=True,
    )
    return False


def send_otp_email(recipient, otp):
  """Sends the OTP and logs it to Render console for instant access."""
  # ALWAYS print to Render console so you can see it in real-time
  print(
      f"\n==================================================",
      flush=True,
  )
  print(f"[OTP CODE] Verification OTP for {recipient} is: {otp}", flush=True)
  print(
      f"==================================================\n",
      flush=True,
  )

  subject = "AirBook - Your Verification OTP"
  body = f"""Hello,

Your AirBook verification code is: {otp}

This code is valid for 10 minutes.

If you did not request this, you can safely ignore this email.

Regards,
AirBook Team
"""
  # Send in background thread so the browser never waits
  t = Thread(target=_send_smtp_email, args=(recipient, subject, body))
  t.daemon = True
  t.start()
  return True


def send_reset_otp_email(recipient, otp):
  """Sends password reset OTP and logs it to Render console."""
  print(
      f"\n==================================================",
      flush=True,
  )
  print(
      f"[RESET OTP] Password Reset OTP for {recipient} is: {otp}", flush=True
  )
  print(
      f"==================================================\n",
      flush=True,
  )

  subject = "AirBook - Password Reset OTP"
  body = f"""Hello,

Your AirBook password reset OTP is: {otp}

This code is valid for 10 minutes.

Regards,
AirBook Team
"""
  t = Thread(target=_send_smtp_email, args=(recipient, subject, body))
  t.daemon = True
  t.start()
  return True