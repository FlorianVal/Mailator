import logging
import logging.config

import yaml
from flask import Flask, request

from utils.mail import MailHandler
from utils.notifications import NotificationManager
from utils.web import webScrap

with open("config/log_config.yaml", "r") as stream:
    config = yaml.safe_load(stream)
logging.config.dictConfig(config)
logging.info(f"Starting app with config : {config}")

app = Flask(__name__)
mail_handler = MailHandler.getInstance()
web_scraper = webScrap.getInstance()
notification_manager = NotificationManager.getInstance()


@app.route("/")
def getMail():
    notification_manager.send_notification("Route GetMail called", request)
    address = mail_handler.GetRandomMailAddress()
    web_scraper.submitForms(address)
    last_mail = mail_handler.WaitForMail(address)

    return mail_handler.HtmlFromMail(last_mail)


if __name__ == "__main__":
    from waitress import serve

    serve(app, host="0.0.0.0", port=5000)
