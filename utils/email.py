import os
import socket
from threading import Thread
import traceback
from flask import current_app
from flask_mail import Mail, Message

mail = Mail()

# ---------------------------------------------------------
# CRITICAL FIX FOR RENDER: Force IPv4 for smtp.gmail.com
# Render Linux drops outbound IPv6 packets, causing Gmail
# SMTP to hang indefinitely and time out.
# ---------------------------------------------------------
_orig_getaddrinfo = socket.getaddrinfo


def _getaddrinfo_ipv4_only(host, port, family=0, type=0, proto=0, flags=0):
  if host and "gmail.com" in str(host).lower():
    family = socket.AF_INET  # Force IPv4
  return _orig_getaddrinfo(host, port, family, type, proto, flags)


socket.getaddrinfo = _getaddrinfo_ipv4_only


def is_mail_configured():
  """Checks whether email configuration variables are present."""
  return all([
      current_app.config.get("MAIL_SERVER"),
      current_app.config.get("MAIL_PORT"),
      current_app.config.get("MAIL_USERNAME"),
      current_app.config.get("MAIL_PASSWORD"),
  ])


def _async_send_task(app, msg):
  """Background thread worker to deliver email without blocking web requests."""
  with app.app_context():
    try:
      mail.send(msg)
      print(
          f"[MAIL SUCCESS] Email delivered to {msg.recipients}",
          flush=True,
      )
    except Exception as e:
      print(f"[MAIL ERROR] Delivery failed: {repr(e)}", flush=True)
      traceback.print_exc()


def send_otp_email(recipient, otp):
  """Sends registration OTP via background thread and logs it for instant testing."""
  username = current_app.config.get("MAIL_USERNAME")

  # Console fallback: Always prints to Render logs so you never get locked out
  print(
      f"\n==================================================",
      flush=True,
  )
  print(f"[AUTH OTP] Registration OTP for {recipient} is: {otp}", flush=True)
  print(
      f"==================================================\n",
      flush=True,
  )

  msg = Message(
      subject="AirBook - Email Verification OTP",
      sender=username,
      recipients=[recipient],
  )
  msg.body = f"""Hello,

Your AirBook verification OTP is: {otp}

This OTP is valid for 5 minutes.

If you did not create an AirBook account, you can safely ignore this email.

Regards,
AirBook Team
"""

  app = current_app._get_current_object()
  thread = Thread(target=_async_send_task, args=(app, msg))
  thread.daemon = True
  thread.start()
  return True


def send_reset_otp_email(recipient, otp):
  """Sends password reset OTP via background thread."""
  username = current_app.config.get("MAIL_USERNAME")

  print(
      f"\n==================================================",
      flush=True,
  )
  print(
      f"[AUTH OTP] Password Reset OTP for {recipient} is: {otp}", flush=True
  )
  print(
      f"==================================================\n",
      flush=True,
  )

  msg = Message(
      subject="AirBook - Password Reset OTP",
      sender=username,
      recipients=[recipient],
  )
  msg.body = f"""Hello,

Your AirBook password reset OTP is: {otp}

This OTP is valid for 5 minutes.

If you did not request a password reset, you can safely ignore this email.

Regards,
AirBook Team
"""

  app = current_app._get_current_object()
  thread = Thread(target=_async_send_task, args=(app, msg))
  thread.daemon = True
  thread.start()
  return Truev