from flask_mail import Mail, Message
from flask import current_app

mail = Mail()


def is_mail_configured():
    return all([
        current_app.config.get("MAIL_SERVER"),
        current_app.config.get("MAIL_PORT"),
        current_app.config.get("MAIL_USERNAME"),
        current_app.config.get("MAIL_PASSWORD")
    ])


def send_otp_email(recipient, otp):

    msg = Message(
        subject="AirBook - Email Verification OTP",
        recipients=[recipient]
    )

    msg.body = f"""
Hello,

Your AirBook verification OTP is:

{otp}

This OTP is valid for 5 minutes.

If you did not create an AirBook account, you can safely ignore this email.

Regards,
AirBook Team
"""

    mail.send(msg)

    return True


def send_reset_otp_email(recipient, otp):

    msg = Message(
        subject="AirBook - Password Reset OTP",
        recipients=[recipient]
    )

    msg.body = f"""
Hello,

We received a request to reset your AirBook password.

Your password reset OTP is:

{otp}

This OTP is valid for 5 minutes.

If you did not request a password reset, you can safely ignore this email.

Regards,
AirBook Team
"""

    mail.send(msg)

    return True