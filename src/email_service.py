import os
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
FROM_EMAIL = os.getenv("FROM_EMAIL", SMTP_USER or "onboarding@resend.dev")


def send_otp_email(to_email: str, otp_code: str) -> tuple[bool, str]:
    """
    Sends an OTP verification email to the given recipient.
    Supports Resend API or direct Gmail / SMTP with SSL / STARTTLS.
    Always flushes OTP to server console immediately.
    """
    # 1. ALWAYS print and flush the OTP to console immediately
    print(f"\n=======================================================", flush=True)
    print(f" [REAL OTP GENERATED FOR: {to_email}]", flush=True)
    print(f" >>> OTP CODE: {otp_code} <<<", flush=True)
    print(f" Valid for: 10 minutes", flush=True)
    print(f"=======================================================\n", flush=True)
    sys.stdout.flush()

    subject = "🎓 Your AVFA Institution Verification Code"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #F7F4EE; margin: 0; padding: 20px; }}
        .email-container {{ max-width: 520px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; border: 1px solid #DDD7CF; border-top: 6px solid #C65D3B; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }}
        .header {{ background: #243B53; color: #ffffff; padding: 25px; text-align: center; }}
        .header h1 {{ margin: 0; font-size: 22px; font-family: Georgia, serif; letter-spacing: 0.5px; }}
        .header p {{ margin: 5px 0 0; font-size: 12px; color: #E5A853; text-transform: uppercase; letter-spacing: 1px; }}
        .content {{ padding: 30px 25px; text-align: center; color: #252525; }}
        .otp-box {{ display: inline-block; background: #F7F4EE; border: 2px dashed #243B53; border-radius: 8px; padding: 15px 35px; margin: 20px 0; font-size: 32px; font-weight: bold; letter-spacing: 8px; color: #243B53; font-family: 'Courier New', monospace; }}
        .footer {{ background: #F7F4EE; padding: 15px; text-align: center; font-size: 12px; color: #706B65; border-top: 1px solid #DDD7CF; }}
      </style>
    </head>
    <body>
      <div class="email-container">
        <div class="header">
          <h1>AVFA ACADEMIA</h1>
          <p>SIH25029 • Tamper-Proof Credential System</p>
        </div>
        <div class="content">
          <h2 style="color: #243B53; margin-top: 0;">Institutional Email Verification</h2>
          <p style="color: #706B65; font-size: 15px;">Please use the following 6-digit One-Time Password (OTP) to complete your institutional onboarding:</p>
          <div class="otp-box">{otp_code}</div>
          <p style="color: #706B65; font-size: 13px; margin-top: 10px;">⚠️ This verification code is confidential and expires in <strong>10 minutes</strong>.</p>
        </div>
        <div class="footer">
          © 2026 Authenticity Validator for Academia (Govt of Jharkhand SIH25029).
        </div>
      </div>
    </body>
    </html>
    """

    # Method A: Gmail / SMTP (if configured in .env)
    if SMTP_HOST and SMTP_USER and SMTP_PASSWORD:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"AVFA Academia <{SMTP_USER}>"
            msg["To"] = to_email
            msg.attach(MIMEText(f"Your AVFA Verification Code is: {otp_code} (Valid for 10 mins)", "plain"))
            msg.attach(MIMEText(html_content, "html"))

            if SMTP_PORT == 465:
                with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=10) as server:
                    server.login(SMTP_USER, SMTP_PASSWORD)
                    server.sendmail(SMTP_USER, to_email, msg.as_string())
            else:
                with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
                    server.starttls()
                    server.login(SMTP_USER, SMTP_PASSWORD)
                    server.sendmail(SMTP_USER, to_email, msg.as_string())

            print(f"[EMAIL SERVICE] [SUCCESS] Real OTP email delivered to {to_email} via SMTP ({SMTP_HOST}).", flush=True)
            return True, f"Email delivered to {to_email} via SMTP."
        except Exception as e:
            print(f"[EMAIL SERVICE] [ERROR] SMTP delivery failed: {e}", flush=True)

    # Method B: Resend API (if configured in .env)
    if RESEND_API_KEY:
        try:
            import resend
            resend.api_key = RESEND_API_KEY
            resend.Emails.send({
                "from": FROM_EMAIL,
                "to": to_email,
                "subject": subject,
                "html": html_content
            })
            print(f"[EMAIL SERVICE] [SUCCESS] Real OTP delivered to {to_email} via Resend API.", flush=True)
            return True, f"Email delivered to {to_email} via Resend."
        except Exception as e:
            print(f"[EMAIL SERVICE] [ERROR] Resend delivery failed: {e}", flush=True)

    return False, "OTP printed to terminal console."