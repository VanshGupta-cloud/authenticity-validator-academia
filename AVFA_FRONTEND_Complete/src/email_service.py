import resend
import os
from dotenv import load_dotenv

load_dotenv()

resend.api_key = os.getenv("RESEND_API_KEY")


def send_otp_email(to_email: str, otp_code: str):
    resend.Emails.send({
        "from": "onboarding@resend.dev",
        "to": to_email,
        "subject": "Your Institution Verification Code",
        "html": f"""
        <p>Your OTP for Authenticity Validator is:</p>
        <h2>{otp_code}</h2>
        <p>This code expires in 10 minutes.</p>
        """
    })