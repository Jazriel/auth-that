"""
    WhatAClass.utils.email
    ~~~~~~~~~~~~~~~~~~~~~~

    Provides email functionality.

    :author: Javier Martínez
"""
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from smtplib import SMTP, SMTPException


class EmailServer(object):
    """Email server object, communicates with the real server with SMTP, and MIME"""

    def __init__(self, config=None):
        """Create the EmailServer object, if the config is not specified upon
        initialization, the config property will have to be called.

        :param dict config: This dict should contain:: str FROM, str PASS, str HOST, int PORT
        """
        self._email = None
        self._password = None
        self._host = None
        self._port = None
        self._send = False
        if config is not None:
            self.config = config

    def send_email(self, email, subject, body):
        """Send an email to the specified address."""
        if not self._send:
            return False
        msg = MIMEMultipart('alternative')
        msg['From'] = self._email
        msg['To'] = email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))
        try:
            with SMTP(host=self._host, port=self._port) as server:
                server.ehlo()
                server.starttls()
                server.login(self._email, self._password)
                server.sendmail(self._email, email, msg.as_string())
                return True
        except Exception:
            return False

    @property
    def config(self):
        """Write-only property that stores the configuration of the email."""
        return None

    @config.setter
    def config(self, cf):
        """Setter of the configuration.

        :param dict cf: This dict should contain:: str FROM, str PASS, str HOST, int PORT"""
        self._email = cf['FROM']
        self._password = cf['PASS']
        self._host = cf['HOST']
        self._port = cf['PORT']
        self._send = True if cf['PASS'] is not None else False


