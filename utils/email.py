from flask_mail import Mail, Message

mail = Mail()


def send_otp_email(recipient, otp):

    msg = Message(
        subject="AirBook - Email Verification Code",
        recipients=[recipient]
    )

    msg.body = f"""
Hello,

Thank you for creating your AirBook account.

Your email verification code is:

{otp}

This code is valid for 5 minutes.

If you did not create a AirBook account, you can safely ignore this email.

Regards,
AirBook Team
"""

    mail.send(msg)


def send_reset_otp_email(recipient, otp):

    msg = Message(
        subject="AirBook - Password Reset Code",
        recipients=[recipient]
    )

    msg.body = f"""
Hello,

We received a request to reset your AirBook password.

Your password reset code is:

{otp}

This code is valid for 5 minutes.

If you did not request a password reset, you can safely ignore this email.

Regards,
AirBook Team
"""

    mail.send(msg)