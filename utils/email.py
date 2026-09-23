from threading import Thread
from flask import current_app
from flask_mail import Mail, Message

mail = Mail()


def is_mail_configured():
  return all([
      current_app.config.get("MAIL_SERVER"),
      current_app.config.get("MAIL_PORT"),
      current_app.config.get("MAIL_USERNAME"),
      current_app.config.get("MAIL_PASSWORD"),
  ])


def _async_send_mail(app, msg):
  with app.app_context():
    try:
      mail.send(msg)
    except Exception as e:
      print("ASYNC OTP EMAIL ERROR:", repr(e))


def send_otp_email(recipient, otp):
  msg = Message(
      subject="AirBook - Email Verification OTP", recipients=[recipient]
  )
  msg.body = f"""Hello,

Your AirBook verification OTP is: {otp}

This OTP is valid for 5 minutes.

If you did not create an AirBook account, you can safely ignore this email.

Regards,
AirBook Team
"""
  # Get actual Flask application instance to pass into thread context
  app = current_app._get_current_object()
  thread = Thread(target=_async_send_mail, args=[app, msg])
  thread.daemon = True
  thread.start()
  return True