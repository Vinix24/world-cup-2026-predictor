#!/usr/bin/env python3
"""Mail PREDICTIONS.md to yourself after the daily run.

Configure in .env (all required to activate; without them this is a no-op):
    MAIL_TO=you@example.com
    SMTP_USER=you@gmail.com
    SMTP_PASS=xxxx xxxx xxxx xxxx     # Gmail app password, not your login
Optional:
    SMTP_HOST=smtp.gmail.com
    SMTP_PORT=465
"""
from __future__ import annotations

import os
import smtplib
import ssl
import sys
from datetime import date
from email.mime.text import MIMEText
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from wkpool.config import load_env  # noqa: E402


def main() -> int:
    load_env()
    to = os.environ.get("MAIL_TO", "").strip()
    user = os.environ.get("SMTP_USER", "").strip()
    password = os.environ.get("SMTP_PASS", "").strip()
    if not (to and user and password):
        print("mail not configured (MAIL_TO/SMTP_USER/SMTP_PASS) — skipping")
        return 0

    body = (ROOT / "PREDICTIONS.md").read_text()
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = f"WK-tips {date.today().isoformat()}"
    msg["From"] = user
    msg["To"] = to

    host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    port = int(os.environ.get("SMTP_PORT", "465"))
    with smtplib.SMTP_SSL(host, port, context=ssl.create_default_context()) as smtp:
        smtp.login(user, password)
        smtp.send_message(msg)
    print(f"mailed PREDICTIONS.md to {to}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
