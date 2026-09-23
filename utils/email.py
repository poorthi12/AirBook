import os
import resend

from flask_mail import Mail

# Keep this so existing app.py does not break
mail = Mail()

# Resend configuration
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "").strip()

RESEND_FROM_EMAIL = os.getenv(
    "RESEND_FROM_EMAIL",
    "onboarding@resend.dev"
).strip()


def is_mail_configured():
    return bool(RESEND_API_KEY)


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

    print("========== RESEND DEBUG ==========")
    print("RESEND API KEY EXISTS:", bool(RESEND_API_KEY))
    print("RESEND API KEY PREFIX:",
          RESEND_API_KEY[:7] if RESEND_API_KEY else "NONE")
    print("RESEND FROM EMAIL:", RESEND_FROM_EMAIL)
    print("RECIPIENT:", recipient)

    if not RESEND_API_KEY:
        print("RESEND_API_KEY NOT SET")
        return False

    try:
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
        print("========== RESEND SUCCESS ==========")

        return True

    except Exception as exc:
        print("========== RESEND ERROR ==========")
        print("RESEND OTP EMAIL ERROR:", repr(exc))
        print("========== END RESEND ERROR ==========")

        return False

def send_reset_otp_email(recipient, otp):

    if not RESEND_API_KEY:
        print("RESEND_API_KEY NOT SET")
        return False

    try:
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