import os

from flask import current_app
from flask_mail import Mail, Message

# Keep this so your existing app.py does not break.
mail = Mail()

# Get Resend API key from environment variable
RESEND_API_KEY = os.getenv("RESEND_API_KEY")

# Email address that Resend will use as sender
RESEND_FROM_EMAIL = os.getenv(
    "RESEND_FROM_EMAIL",
    "onboarding@resend.dev"
)


def is_mail_configured():
    return bool((RESEND_API_KEY and str(RESEND_API_KEY).strip()) or (os.getenv("MAIL_USERNAME") and os.getenv("MAIL_PASSWORD")))


def _build_otp_html(title, message, otp):
    return f"""
    <html>
        <body style="
            font-family: Arial, sans-serif;
            background-color: #f4f6f8;
            padding: 30px;
        ">

            <div style="
                max-width: 500px;
                margin: auto;
                background: white;
                padding: 30px;
                border-radius: 12px;
            ">

                <h2 style="color: #111827;">{title}</h2>

                <p>Hello,</p>

                <p>{message}</p>

                <p>Your code is:</p>

                <div style="
                    font-size: 32px;
                    font-weight: bold;
                    letter-spacing: 8px;
                    text-align: center;
                    padding: 20px;
                    background: #f3f4f6;
                    border-radius: 10px;
                    margin: 20px 0;
                ">
                    {otp}
                </div>

                <p>This code is valid for <strong>5 minutes</strong>.</p>

                <p>If you did not request this, you can safely ignore this email.</p>

                <p>
                    Regards,<br>
                    <strong>AirBook Team</strong>
                </p>

            </div>

        </body>
    </html>
    """


def _send_via_smtp(subject, recipient, html_body):
    if not os.getenv("MAIL_USERNAME") or not os.getenv("MAIL_PASSWORD"):
        return False

    try:
        msg = Message(
            subject=subject,
            recipients=[recipient],
            html=html_body,
            sender=os.getenv("MAIL_DEFAULT_SENDER") or os.getenv("MAIL_USERNAME")
        )

        with current_app.app_context():
            mail.send(msg)

        print("SMTP OTP EMAIL SENT TO:", recipient)
        return True
    except Exception as exc:
        print("SMTP EMAIL ERROR:", exc)
        return False


def send_otp_email(recipient, otp):
    subject = "AirBook - Email Verification Code"
    html = _build_otp_html(
        "AirBook Email Verification",
        "Thank you for creating your AirBook account. Your email verification code is:",
        otp,
    )

    if RESEND_API_KEY:
        try:
            import resend

            resend.api_key = RESEND_API_KEY

            params = {
                "from": RESEND_FROM_EMAIL,
                "to": [recipient],
                "subject": subject,
                "html": html,
            }

            response = resend.Emails.send(params)
            print("OTP EMAIL SENT VIA RESEND:", response)
            return True
        except Exception as exc:
            print("RESEND OTP EMAIL ERROR:", exc)

    return _send_via_smtp(subject, recipient, html)


def send_reset_otp_email(recipient, otp):
    subject = "AirBook - Password Reset Code"
    html = _build_otp_html(
        "AirBook Password Reset",
        "We received a request to reset your AirBook password. Your password reset code is:",
        otp,
    )

    if RESEND_API_KEY:
        try:
            import resend

            resend.api_key = RESEND_API_KEY

            params = {
                "from": RESEND_FROM_EMAIL,
                "to": [recipient],
                "subject": subject,
                "html": html,
            }

            response = resend.Emails.send(params)
            print("RESET OTP EMAIL SENT VIA RESEND:", response)
            return True
        except Exception as exc:
            print("RESEND RESET EMAIL ERROR:", exc)

    return _send_via_smtp(subject, recipient, html)
