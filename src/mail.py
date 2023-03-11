import os
from dataclasses import dataclass
from typing import Any

from mailersend import emails

_MAIL_API_KEY = os.environ.get("MAIL_API_KEY")
_MAIN_FROM = "noreply@whatbikeswin.com"


@dataclass
class BaseConfig:
    template_id: str
    subject: str


class SignupConfig(BaseConfig):
    template_id: str = "zr6ke4n9yqvlon12"
    subject: str = "Welcome"


class TempPasswordConfig(BaseConfig):
    template_id: str = "0p7kx4xk557g9yjr"
    subject: str = "Password Reset"


_CONFIGS = {
    "signup": SignupConfig,
    "temp-password": TempPasswordConfig,
}


def send_mail(to: str, config_name: str, variables: dict | None = None) -> Any:
    variables = variables or {}
    config = _CONFIGS[config_name]
    mailer = emails.NewEmail(_MAIL_API_KEY)
    mail_body: dict[str, Any] = {}
    mail_from = {
        "name": "What Bikes Win?",
        "email": "noreply@whatbikeswin.com",
    }
    recipients = [
        {
            "name": "",
            "email": to,
        }
    ]
    personalization = [
        {
            "email": to,
            "substitutions": [
                {"var": key, "value": value} for key, value in variables.items()
            ],
        }
    ]
    mailer.set_mail_from(mail_from, mail_body)
    mailer.set_mail_to(recipients, mail_body)
    mailer.set_subject(config.subject, mail_body)
    mailer.set_simple_personalization(personalization, mail_body)
    mailer.set_template(config.template_id, mail_body)
    return mailer.send(mail_body)
