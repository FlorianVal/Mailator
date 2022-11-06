import logging
import yaml
import logging.config

from flask import Flask
from utils.mail import MailHandler
from utils.web import webScrap

with open('config/log_config.yaml', 'r') as stream:
    config = yaml.load(stream, Loader=yaml.FullLoader)
logging.config.dictConfig(config)


app = Flask(__name__)
mail_handler = MailHandler.getInstance()
web_scraper = webScrap.getInstance()


@app.route("/")
def getMail():

    address = mail_handler.GetRandomMailAddress()
    web_scraper.submitForms(address)
    last_mail = mail_handler.WaitForMail(address)

    return mail_handler.HtmlFromMail(last_mail)


if __name__ == "__main__":
    app.run(debug=True)
