from flask_mail import Mail, Message

mail = Mail()


def is_mail_configured():
    from config import MAIL_SERVER, MAIL_USERNAME, MAIL_PASSWORD
    return bool(MAIL_SERVER and MAIL_USERNAME and MAIL_PASSWORD)


def send_otp_email(recipient, otp):
    if not is_mail_configured():
        print("MAIL CONFIG NOT SET - Skipping OTP email send")
        return False

    try:
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
        return True
    except Exception as exc:
        print("OTP EMAIL ERROR:", exc)
        return False


def send_reset_otp_email(recipient, otp):
    if not is_mail_configured():
        print("MAIL CONFIG NOT SET - Skipping reset OTP email send")
        return False

    try:
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
        return True
    except Exception as exc:
        print("RESET EMAIL ERROR:", exc)
        return False