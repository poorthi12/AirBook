import os

from flask_mail import Mail, Message


mail = Mail()


def send_otp_email(recipient, otp):

    msg = Message(
        subject="AirBook - Email Verification OTP",
        recipients=[recipient]
    )

    msg.body = f"""
Hello,

Your SkyBook verification OTP is:

{otp}

This OTP is valid for 5 minutes.

If you did not create a SkyBook account, you can safely ignore this email.

Regards,
SkyBook Team
"""

    mail.send(msg)


def send_reset_otp_email(recipient, otp):

    msg = Message(
        subject="AirBook - Password Reset OTP",
        recipients=[recipient]
    )

    msg.body = f"""
Hello,

We received a request to reset your SkyBook password.

Your password reset OTP is:

{otp}

This OTP is valid for 5 minutes.

If you did not request a password reset, you can safely ignore this email.

Regards,
SkyBook Team
"""

    mail.send(msg)