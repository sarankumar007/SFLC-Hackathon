#!/usr/bin/env python3
"""
send_email.py

Usage:
  1) Set environment variables:
       EMAIL_USERNAME - your SMTP username (often your email)
       EMAIL_PASSWORD - your SMTP password or app-password
       SMTP_SERVER    - e.g. smtp.gmail.com
       SMTP_PORT      - e.g. 587 (STARTTLS) or 465 (SSL)
     Optionally create a .env file and use python-dotenv (example below).

  2) Run:
       python send_email.py
"""

import os
import sys
import mimetypes
from email.message import EmailMessage
from email.utils import make_msgid
import smtplib
from dotenv import load_dotenv
load_dotenv("secrets.env")  

# Optional: load .env if you prefer (uncomment if you install python-dotenv)
# from dotenv import load_dotenv
# load_dotenv()

def build_message(
    subject: str,
    body: str,
    from_addr: str,
    to_addrs: list,
    cc_addrs: list = None,
    bcc_addrs: list = None,
    html: bool = False,
    attachments: list = None
) -> EmailMessage:
    """Build an EmailMessage with optional HTML and attachments.
    attachments: list of file paths
    """
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = ", ".join(to_addrs) if isinstance(to_addrs, (list, tuple)) else to_addrs
    if cc_addrs:
        msg["Cc"] = ", ".join(cc_addrs)

    # Set body: if html True, set alternative with text fallback
    if html:
        # Create a plain-text fallback (simple)
        plain = _html_to_plaintext(body)
        msg.set_content(plain)
        msg.add_alternative(body, subtype="html")
    else:
        msg.set_content(body)

    # Attach files
    if attachments:
        for path in attachments:
            if not os.path.isfile(path):
                print(f"Warning: attachment not found -> {path}", file=sys.stderr)
                continue
            ctype, encoding = mimetypes.guess_type(path)
            if ctype is None:
                ctype = "application/octet-stream"
            maintype, subtype = ctype.split("/", 1)
            with open(path, "rb") as f:
                data = f.read()
            filename = os.path.basename(path)
            msg.add_attachment(data, maintype=maintype, subtype=subtype, filename=filename)

    return msg

def _html_to_plaintext(html: str) -> str:
    # Minimal fallback: strip tags for simple HTML. For production consider html2text package.
    import re
    text = re.sub(r"<br\s*/?>", "\n", html, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\n\s+\n", "\n\n", text)
    return text.strip()

def send_email(
    smtp_server: str,
    smtp_port: int,
    username: str,
    password: str,
    msg: EmailMessage,
    use_ssl: bool = False,
    timeout: int = 60
) -> None:
    """Send message using SMTP. If use_ssl True, connects using SMTP_SSL (port 465 typical).
    Otherwise uses STARTTLS (port 587 typical).
    """
    all_recipients = []
    for hdr in ("To", "Cc"):
        if hdr in msg:
            all_recipients += [addr.strip() for addr in msg[hdr].split(",") if addr.strip()]
    # Include BCC if present (not in headers)
    if hasattr(msg, "bcc") and msg.bcc:
        all_recipients += msg.bcc
    # If user passed BCC separately, they should be appended to the list by caller.

    if use_ssl:
        server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=timeout)
    else:
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=timeout)

    try:
        server.set_debuglevel(0)  # set to 1 to see SMTP debug output
        if not use_ssl:
            server.ehlo()
            server.starttls()
            server.ehlo()
        server.login(username, password)
        server.send_message(msg)
        print("Email sent successfully.")
    except smtplib.SMTPException as e:
        print("Error sending email:", e, file=sys.stderr)
        raise
    finally:
        try:
            server.quit()
        except Exception:
            pass

def example_usage():
    # Read configuration from environment (recommended)
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    EMAIL_USERNAME = os.getenv("EMAIL_USERNAME")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

    if not EMAIL_USERNAME or not EMAIL_PASSWORD:
        print("ERROR: EMAIL_USERNAME and EMAIL_PASSWORD must be set in environment.", file=sys.stderr)
        sys.exit(1)

    from_addr = EMAIL_USERNAME
    to_addrs = ["santyraj26@gmail.com"]  # replace with real recipient(s)
    cc_addrs = []
    bcc_addrs = ["hidden@example.com"]  # optional

    subject = "Test email from Python"
    html_body = """
    <html>
      <body>
        <h2>Hello 👋</h2>
        <p>This is a <b>test</b> email sent from a Python script.</p>
      </body>
    </html>
    """

    attachments = []  # e.g. ["./file.pdf", "./image.png"]

    msg = build_message(
        subject=subject,
        body=html_body,
        from_addr=from_addr,
        to_addrs=to_addrs,
        cc_addrs=cc_addrs,
        bcc_addrs=bcc_addrs,
        html=True,
        attachments=attachments
    )

    # If you want to include bcc in sending but not headers:
    # msg.bcc = bcc_addrs  # note: EmailMessage doesn't officially have bcc header; we add attribute for send recipients
    # But the recipients are determined automatically by send_message, which collects addresses from headers.
    # To ensure bcc gets sent, we will include them when calling server.send_message (send_message inspects recipients).
    # The simplest approach is to set msg["Bcc"] (it won't appear in received headers) OR pass recipients when sending.
    if bcc_addrs:
        # Add Bcc header so send_message picks them up (won't appear in final displayed headers often)
        msg["Bcc"] = ", ".join(bcc_addrs)

    use_ssl = (SMTP_PORT == 465)
    send_email(SMTP_SERVER, SMTP_PORT, EMAIL_USERNAME, EMAIL_PASSWORD, msg, use_ssl=use_ssl)

if __name__ == "__main__":
    example_usage()




def send_email_function(to_addrs: list, subject: str, body: str, html: bool = True, attachments: list = None):
    """
    Simplified function to send an email with environment configs.
    """
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    EMAIL_USERNAME = os.getenv("EMAIL_USERNAME")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

    if not EMAIL_USERNAME or not EMAIL_PASSWORD:
        raise ValueError("EMAIL_USERNAME and EMAIL_PASSWORD must be set in environment")

    from_addr = EMAIL_USERNAME

    msg = build_message(
        subject=subject,
        body=body,
        from_addr=from_addr,
        to_addrs=to_addrs,
        html=html,
        attachments=attachments
    )

    use_ssl = (SMTP_PORT == 465)
    send_email(SMTP_SERVER, SMTP_PORT, EMAIL_USERNAME, EMAIL_PASSWORD, msg, use_ssl=use_ssl)
