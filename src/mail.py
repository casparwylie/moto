import os
from typing import Any

from mailersend import emails

MAIL_API_KEY = os.environ.get("MAIL_API_KEY")
print(MAIL_API_KEY)


def send_email(subject: str, to: str, html: str) -> Any:
    mailer = emails.NewEmail(MAIL_API_KEY)
    mail_body: dict[str, Any] = {}
    mail_from = {
        "name": "",
        "email": "noreply@whatbikeswin.com",
    }
    recipients = [
        {
            "name": "",
            "email": to,
        }
    ]
    mailer.set_mail_from(mail_from, mail_body)
    mailer.set_mail_to(recipients, mail_body)
    mailer.set_subject(subject, mail_body)
    mailer.set_html_content(html, mail_body)
    return mailer.send(mail_body)
