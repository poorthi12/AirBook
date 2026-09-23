import os

from flask_mail import Mail, Message

try:
    import resend
except Exception:
    resend = None

# Keep this so existing app.py does not break
mail = Mail()

# SMTP / Gmail configuration (preferred for no-domain setup)
MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com").strip()
MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
MAIL_USE_TLS = str(os.getenv("MAIL_USE_TLS", "True")).strip().lower() in {"1", "true", "yes", "on"}
MAIL_USERNAME = os.getenv("MAIL_USERNAME", "").strip()
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "").strip()
MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", MAIL_USERNAME or "").strip()

# Resend configuration
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "").strip()
RESEND_FROM_EMAIL = os.getenv(
    "RESEND_FROM_EMAIL",
    "onboarding@resend.dev"
).strip()


def is_mail_configured():
    smtp_ready = bool(MAIL_USERNAME and MAIL_PASSWORD)
    resend_ready = bool(RESEND_API_KEY and RESEND_FROM_EMAIL and RESEND_FROM_EMAIL != "onboarding@resend.dev")
    return smtp_ready or resend_ready


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


def send_otp_email(recipient, otp):

    if MAIL_USERNAME and MAIL_PASSWORD:
        try:
            from flask import current_app
            msg = Message(
                subject="AirBook - Email Verification Code",
                recipients=[recipient],
                html=_build_otp_html(
                    "AirBook Email Verification",
                    "Thank you for creating your AirBook account. Your email verification code is:",
                    otp
                ),
                sender=MAIL_DEFAULT_SENDER or MAIL_USERNAME,
            )
            mail.send(msg)
            print("OTP EMAIL SENT VIA SMTP:", recipient)
            return True
        except Exception as exc:
            print("SMTP OTP EMAIL ERROR:", repr(exc))
            return False

    if not RESEND_API_KEY:
        print("NO EMAIL PROVIDER CONFIGURED")
        return False

    try:
        if resend is None:
            print("Resend library not installed")
            return False

        resend.api_key = RESEND_API_KEY

        params = {
            "from": RESEND_FROM_EMAIL,
            "to": [recipient],
            "subject": "AirBook - Email Verification Code",
            "html": _build_otp_html(
                "AirBook Email Verification",
                "Thank you for creating your AirBook account. Your email verification code is:",
                otp
            )
        }

        response = resend.Emails.send(params)

        print("OTP EMAIL SENT VIA RESEND:", response)
        return True

    except Exception as exc:
        print("RESEND OTP EMAIL ERROR:", repr(exc))
        return False


def send_reset_otp_email(recipient, otp):

    if MAIL_USERNAME and MAIL_PASSWORD:
        try:
            msg = Message(
                subject="AirBook - Password Reset Code",
                recipients=[recipient],
                html=_build_otp_html(
                    "AirBook Password Reset",
                    "We received a request to reset your AirBook password. Your password reset code is:",
                    otp
                ),
                sender=MAIL_DEFAULT_SENDER or MAIL_USERNAME,
            )
            mail.send(msg)
            print("RESET OTP EMAIL SENT VIA SMTP:", recipient)
            return True
        except Exception as exc:
            print("SMTP RESET EMAIL ERROR:", exc)
            return False

    if not RESEND_API_KEY:
        print("NO EMAIL PROVIDER CONFIGURED")
        return False

    try:
        if resend is None:
            print("Resend library not installed")
            return False

        resend.api_key = RESEND_API_KEY

        params = {
            "from": RESEND_FROM_EMAIL,
            "to": [recipient],
            "subject": "AirBook - Password Reset Code",
            "html": _build_otp_html(
                "AirBook Password Reset",
                "We received a request to reset your AirBook password. Your password reset code is:",
                otp
            )
        }

        response = resend.Emails.send(params)

        print("RESET OTP EMAIL SENT VIA RESEND:", response)

        return True

    except Exception as exc:
        print("RESEND RESET EMAIL ERROR:", exc)
        return False