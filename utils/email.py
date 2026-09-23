from threading import Thread
import traceback
from flask import current_app
from flask_mail import Mail, Message

mail = Mail()


def is_mail_configured():
  """Checks whether email configuration variables are present."""
  return all([
      current_app.config.get("MAIL_SERVER"),
      current_app.config.get("MAIL_PORT"),
      current_app.config.get("MAIL_USERNAME"),
      current_app.config.get("MAIL_PASSWORD"),
  ])


def _async_send_email_task(app, msg):
  """Background thread worker to deliver email with forced log flushing."""
  with app.app_context():
    try:
      mail.send(msg)
      print(
          f"[MAIL SUCCESS] OTP email successfully sent to {msg.recipients}",
          flush=True,
      )
    except Exception as e:
      print(f"[MAIL ERROR] Async send failed: {repr(e)}", flush=True)
      traceback.print_exc()


def send_otp_email(recipient, otp):
  """Composes and dispatches the OTP email in a background thread."""
  username = current_app.config.get("MAIL_USERNAME")

  # Gmail REQUIRES the sender to match the authenticated Gmail username
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
  email_thread = Thread(target=_async_send_email_task, args=(app, msg))
  email_thread.daemon = True
  email_thread.start()
  return True


def test_smtp_connection(recipient):
  """Synchronous test function to return the exact SMTP error to the browser."""
  username = current_app.config.get("MAIL_USERNAME")
  msg = Message(
      subject="AirBook - SMTP Test", sender=username, recipients=[recipient]
  )
  msg.body = "This is a direct SMTP test from AirBook on Render."

  try:
    mail.send(msg)
    return {
        "status": "success",
        "message": f"Email successfully sent to {recipient}!",
    }
  except Exception as e:
    return {
        "status": "error",
        "error_type": type(e).__name__,
        "error_message": str(e),
        "config_used": {
            "server": current_app.config.get("MAIL_SERVER"),
            "port": current_app.config.get("MAIL_PORT"),
            "use_ssl": current_app.config.get("MAIL_USE_SSL"),
            "use_tls": current_app.config.get("MAIL_USE_TLS"),
            "username": current_app.config.get("MAIL_USERNAME"),
            "password_configured": bool(
                current_app.config.get("MAIL_PASSWORD")
            ),
        },
    }