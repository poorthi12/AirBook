import os
import resend

from flask_mail import Mail

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
    return bool(RESEND_API_KEY)


def send_otp_email(recipient, otp):

    if not RESEND_API_KEY:
        print("RESEND_API_KEY NOT SET")
        return False

    try:

        resend.api_key = RESEND_API_KEY

        params = {
            "from": RESEND_FROM_EMAIL,
            "to": [recipient],
            "subject": "AirBook - Email Verification Code",
            "html": f"""
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

                        <h2 style="color: #111827;">
                            AirBook Email Verification
                        </h2>

                        <p>Hello,</p>

                        <p>
                            Thank you for creating your AirBook account.
                        </p>

                        <p>
                            Your email verification code is:
                        </p>

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

                        <p>
                            This code is valid for <strong>5 minutes</strong>.
                        </p>

                        <p>
                            If you did not create an AirBook account,
                            you can safely ignore this email.
                        </p>

                        <p>
                            Regards,<br>
                            <strong>AirBook Team</strong>
                        </p>

                    </div>

                </body>
            </html>
            """
        }

        response = resend.Emails.send(params)

        print("OTP EMAIL SENT:", response)

        return True

    except Exception as exc:

        print("OTP EMAIL ERROR:", exc)

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
            "html": f"""
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

                        <h2 style="color: #111827;">
                            AirBook Password Reset
                        </h2>

                        <p>Hello,</p>

                        <p>
                            We received a request to reset your AirBook password.
                        </p>

                        <p>
                            Your password reset code is:
                        </p>

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

                        <p>
                            This code is valid for <strong>5 minutes</strong>.
                        </p>

                        <p>
                            If you did not request a password reset,
                            you can safely ignore this email.
                        </p>

                        <p>
                            Regards,<br>
                            <strong>AirBook Team</strong>
                        </p>

                    </div>

                </body>
            </html>
            """
        }

        response = resend.Emails.send(params)

        print("RESET OTP EMAIL SENT:", response)

        return True

    except Exception as exc:

        print("RESET EMAIL ERROR:", exc)

        return False
