"""
Test script to verify real email delivery via Gmail SMTP or Resend API.
Usage: python test_email.py your_email@gmail.com
"""

import sys
from src.email_service import send_otp_email

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "arpitkesharwani29@gmail.com"
    print(f"\n--- Testing Real Email Delivery to: {target} ---")
    
    success, message = send_otp_email(target, "742918")
    
    if success:
        print(f"\n[SUCCESS] An email was successfully delivered to {target}! Check your inbox/spam folder.")
    else:
        print(f"\n[NOTICE] Email was not dispatched to inbox because credentials are not yet set in .env.")
        print(f"To enable real Gmail delivery, add your credentials to the .env file in this directory.")
