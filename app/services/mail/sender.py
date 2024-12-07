import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.services.mail import template
from app.services.mail.config import SMTP_SERVER, SMTP_PORT, SMTP_USER, SMTP_PASSWORD


async def send_email(to_email: str, reset_link: str):
    msg = MIMEMultipart()
    msg["From"] = SMTP_USER
    msg["To"] = to_email
    msg["Subject"] = "Password Reset Request"

    body = template.html_content(reset_link)

    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()  # Secure the connection
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
    except Exception as e:
        print(f"Failed to send email: {e}")