from bs4 import BeautifulSoup
from requests_html import HTMLSession
from urllib.parse import urljoin

import yaml
import random
import logging


class webScrap(object):

    __shared_instance = None

    @staticmethod
    def getInstance():
        """Static Access Method"""
        if webScrap.__shared_instance == None:
            webScrap()
        return webScrap.__shared_instance

    def __init__(self):
        """virtual private constructor"""
        if webScrap.__shared_instance != None:
            raise Exception("This class is a singleton class !")
        else:
            webScrap.__shared_instance = self
            self.__getConfig()
        self.__newSession()

    def __getConfig(self):
        with open('config/config.yaml') as yaml_data_file:
            self.config = yaml.load(
                yaml_data_file, Loader=yaml.FullLoader).get("Web")

    def __newSession(self):
        self.session = HTMLSession()

    def __getAllForms(self, url=None):

        res = self.session.get(url)

        # for javascript driven website
        # res.html.render()

        soup = BeautifulSoup(res.html.html, "html.parser")
        return soup.find_all("form")

    @staticmethod
    def __getFormDetails(form):
        """Returns the HTML details of a form,
        including action, method and list of form controls (inputs, etc)"""

        details = {}
        # get the form action (requested URL)
        action = form.attrs.get("action").lower()
        # get the form method (POST, GET, DELETE, etc)
        # if not specified, GET is the default in HTML
        method = form.attrs.get("method", "get").lower()
        # get all form inputs
        inputs = []
        for input_tag in form.find_all("input"):
            # get type of input form control
            input_type = input_tag.attrs.get("type", "text")
            # get name attribute
            input_name = input_tag.attrs.get("name")
            # get the default value of that input tag
            input_value = input_tag.attrs.get("value", "")
            # add everything to that list
            inputs.append(
                {"type": input_type, "name": input_name, "value": input_value})
        # put everything to the resulting dictionary
        details["action"] = action
        details["method"] = method
        details["inputs"] = inputs
        return details

    def submitForms(self, email, first_name=None, last_name=None):

        self.__newSession()

        if type(self.config.get("Urls")) is list:
            url = random.choice(self.config.get("Urls"))
        else:
            url = self.config.get("Urls")

        if first_name is None or last_name is None:
            first_name, last_name = self.getNameFromMail(email)

        logging.info(
            f"Submit form to {url} with : {email}, first_name: {first_name}, last_name: {last_name}")

        forms = self.__getAllForms(url)

        self.__checkFormsDetails(forms)

        if len(forms) == 1:
            form_details = self.__getFormDetails(forms[0])
        else:
            raise Exception("Multiple Forms found on page")

        # the data body we want to submit
        data = {self.config.get("Form").get("FirstName"): first_name,
                self.config.get("Form").get("LastName"): last_name,
                self.config.get("Form").get("Mail0"): email,
                self.config.get("Form").get("Mail1"): email}

        for input_tag in form_details["inputs"]:
            if input_tag["type"] == "hidden" or input_tag["type"] == "submit":
                # if it's hidden, use the default value
                data[input_tag["name"]] = input_tag["value"]

        url = urljoin(url, form_details["action"])

        if form_details["method"] == "post":
            res = self.session.post(url, data=data)
        elif form_details["method"] == "get":
            res = self.session.get(url, params=data)
        logging.info(f"Form posted res : {res.status_code}")
        return res.text

    def __checkFormsDetails(self, forms):
        for i, form in enumerate(forms):
            form_details = self.__getFormDetails(form)
            logging.info(f"Action of form : {form_details['action']}")
            logging.info(f"Method of form : {form_details['method']}")
            logging.info(
                f"Hidden inputs : {len([input for input in form_details['inputs'] if input['type'] == 'hidden'])}")

            inputs = [input for input in form_details["inputs"]
                      if input["type"] != 'hidden' and input["type"] != "submit"]

            name_in_conf = list(self.config.get("Form").values())
            inputs_name = list(map(lambda x: x["name"], inputs))
            if len(set(name_in_conf) - set(inputs_name)) != 0:
                logging.warning(
                    f"Name in Form conf not found in inputs : {set(name_in_conf) - set(inputs_name)}")
            if len(set(inputs_name) - set(name_in_conf)) != 0:
                logging.warning(
                    f"Name in inputs not found in conf : {set(inputs_name) - set(name_in_conf)}")

    @staticmethod
    def getNameFromMail(email):
        try:
            a, b = email.split(
                "@")[0].split("_")[0], email.split("@")[0].split("_")[1]
        except IndexError:
            a, b = email.split("@")[0][:len(email.split("@")[0]) //
                                       2], email.split("@")[0][len(email.split("@")[0])//2:]
        return a, b
