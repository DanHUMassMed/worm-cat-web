import smtplib
from socket import gaierror
from email.mime.text import MIMEText
import ssl
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
import logging
import os

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

SMTP_SERVER = "smtp.gmail.com"
SMTP_LOGIN = "wormcat.emailer@gmail.com"
SMTP_PASSWD = "irimdclrzuytkpja"  # App Password


def email_results(receiver, the_file):
    index_of_sep = the_file.rfind(os.path.sep)
    filename = the_file[index_of_sep + 1:-4]

    subject = 'Wormcat Results for {}'.format(filename)
    sender = "wormcat@gmail.com"
    message_text = """
    Please find attached the results of your run.

    Please do NOT respond to this message as this email address is not monitored.

    Thank you for using wormcat.com!
    """
    message = construct_message_with_attachment(subject, sender, receiver, message_text, the_file)
    send_message_ssl(sender, receiver, message)


def construct_message_with_html(subject, sender, receiver, message_text=None, message_html=None):
    the_message = MIMEMultipart()
    the_message['Subject'] = subject
    the_message['To'] = receiver
    the_message['From'] = sender
    the_message.preamble = 'I am not using a MIME-aware mail reader.\n'

    if message_text:
        the_message.attach(MIMEText(message_text, "plain"))
    if message_html:
        the_message.attach(MIMEText(message_html, "html"))

    return the_message.as_string()


def construct_message_with_attachment(subject, sender, receiver, message_text, the_file):
    zip_file = open(the_file, 'rb')
    the_message = MIMEMultipart()
    the_message['Subject'] = subject
    the_message['To'] = receiver
    the_message['From'] = sender
    the_message.preamble = 'I am not using a MIME-aware mail reader.\n'

    the_message.attach(MIMEText(message_text, "plain"))

    msg = MIMEBase('application', 'zip')
    msg.set_payload(zip_file.read())
    encoders.encode_base64(msg)

    index_of_sep = the_file.rfind(os.path.sep)
    msg.add_header('Content-Disposition', 'attachment', filename=the_file[index_of_sep+1:])
    the_message.attach(msg)
    return the_message.as_string()


def send_message(sender, receiver, message):
    try:
        port = 587
        with smtplib.SMTP(SMTP_SERVER, port) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_LOGIN, SMTP_PASSWD)
            server.sendmail(sender, receiver, message)
    except (gaierror, ConnectionRefusedError):
        logging.debug("Failed to connect to the server. Bad connection settings?")
    except smtplib.SMTPServerDisconnected:
        logging.debug("Failed to connect to the server. Wrong user/password?")
    except smtplib.SMTPException as e:
        logging.debug("SMTP error occurred: {}".format(str(e)))
    else:
        logging.debug("SMTP sent to: {}".format(receiver))


def send_message_ssl(sender, receiver, message):
    try:
        port = 465
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_SERVER, port, context=context) as server:
            server.login(SMTP_LOGIN, SMTP_PASSWD)
            server.sendmail(sender, receiver, message)
    except (gaierror, ConnectionRefusedError):
        logging.debug("Failed to connect to the server. Bad connection settings?")
    except smtplib.SMTPServerDisconnected:
        logging.debug("Failed to connect to the server. Wrong user/password?")
    except smtplib.SMTPException as e:
        logging.debug("SMTP error occurred: {}".format(str(e)))
    else:
        logging.debug("SMTP sent to: {}".format(receiver))


def main():
    sender = "wormcat@gmail.com"
    receiver = "daniel.higgins@yahoo.com"
    the_file = "README.md.zip"
    html = """<html> <body> <p>Hi,<br> Check out our new search engine:</p> 
    <p><a href="http://google.com">Google</a></p> 
    <p> Feel free to <strong>let us</strong> know if you like it!</p> </body> </html> """

    message = construct_message_with_html(subject="Hello Subject!",
                                          sender=sender,
                                          receiver=receiver,
                                          message_text="This is a test!!",
                                          message_html=html)
    send_message_ssl(sender, receiver, message)


if __name__ == "__main__":
    main()