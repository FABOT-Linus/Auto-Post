"""
email_reader.py
Connects to an IMAP mailbox, finds today's newsletter email (filtered by
sender / subject), and returns its plain-text content.
"""

import imaplib
import email
from email.header import decode_header
from datetime import date
from bs4 import BeautifulSoup
import os


def _decode(value):
    if value is None:
        return ""
    parts = decode_header(value)
    out = ""
    for text, enc in parts:
        if isinstance(text, bytes):
            out += text.decode(enc or "utf-8", errors="ignore")
        else:
            out += text
    return out


def _html_to_text(html):
    soup = BeautifulSoup(html, "html.parser")
    # Drop scripts/styles which add noise
    for tag in soup(["script", "style"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    # Collapse excess blank lines
    lines = [ln.strip() for ln in text.splitlines()]
    lines = [ln for ln in lines if ln]
    return "\n".join(lines)


def _extract_body(msg):
    """Prefer plain text; fall back to converting HTML."""
    if msg.is_multipart():
        plain, html = None, None
        for part in msg.walk():
            ctype = part.get_content_type()
            disp = str(part.get("Content-Disposition") or "")
            if "attachment" in disp:
                continue
            if ctype == "text/plain" and plain is None:
                plain = part.get_payload(decode=True).decode(
                    part.get_content_charset() or "utf-8", errors="ignore"
                )
            elif ctype == "text/html" and html is None:
                html = part.get_payload(decode=True).decode(
                    part.get_content_charset() or "utf-8", errors="ignore"
                )
        if plain and plain.strip():
            return plain
        if html:
            return _html_to_text(html)
        return ""
    else:
        payload = msg.get_payload(decode=True)
        charset = msg.get_content_charset() or "utf-8"
        text = payload.decode(charset, errors="ignore") if payload else ""
        if msg.get_content_type() == "text/html":
            return _html_to_text(text)
        return text


def fetch_todays_newsletter():
    """
    Returns the plain-text content of today's matching email, or None
    if nothing was found.
    """
    imap_server = os.environ["EMAIL_IMAP_SERVER"]
    address = os.environ["EMAIL_ADDRESS"]
    app_password = os.environ["EMAIL_APP_PASSWORD"]
    sender_filter = os.environ.get("EMAIL_SENDER_FILTER", "").strip()
    subject_filter = os.environ.get("EMAIL_SUBJECT_FILTER", "").strip()

    conn = imaplib.IMAP4_SSL(imap_server)
    conn.login(address, app_password)
    conn.select("INBOX")

    today_str = date.today().strftime("%d-%b-%Y")  # IMAP date format
    criteria = ["SINCE", today_str]
    if sender_filter:
        criteria += ["FROM", f'"{sender_filter}"']
    if subject_filter:
        criteria += ["SUBJECT", f'"{subject_filter}"']

    status, data = conn.search(None, *criteria)
    if status != "OK" or not data[0]:
        conn.logout()
        return None

    ids = data[0].split()
    latest_id = ids[-1]  # most recent match

    status, msg_data = conn.fetch(latest_id, "(RFC822)")
    conn.logout()
    if status != "OK":
        return None

    raw_email = msg_data[0][1]
    msg = email.message_from_bytes(raw_email)
    subject = _decode(msg.get("Subject"))
    body = _extract_body(msg)

    return {"subject": subject, "body": body}


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    result = fetch_todays_newsletter()
    if result:
        print("Subject:", result["subject"])
        print("---")
        print(result["body"][:2000])
    else:
        print("No matching email found for today.")
