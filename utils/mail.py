import requests
import logging
import yaml
import names
import random
import ast
import hashlib
import time
import os
from datetime import datetime

import json


class MailHandler(object):
 
    __shared_instance = None
 
    @staticmethod
    def getInstance():
 
        """Static Access Method"""
        if MailHandler.__shared_instance == None:
            MailHandler()
        return MailHandler.__shared_instance
 
    def __init__(self):
 
        """virtual private constructor"""
        if MailHandler.__shared_instance != None:
            raise Exception ("This class is a singleton class !")
        else:
            MailHandler.__shared_instance = self
            self.__getConfig()
        self.managed_address = []

    def __usageMeasurement(func):
        def Measurement(self, *args):
            LogsUsagePath = "logs/UsageLogs.log"
            try:
                with open(LogsUsagePath, "r") as stream:
                    data = stream.read()
                self.measurements = json.loads(data)
            except FileNotFoundError:
                pass

            out = func(self, *args)
            if hasattr(self, "measurements") and out in self.measurements:
                self.measurements[out] += 1
            elif hasattr(self, "measurements"):
                self.measurements.update({out: 1})
            else:
                self.measurements = {out: 1}
            logging.info(f"Usage metrics : {self.measurements}")
            if not os.path.exists(LogsUsagePath):
                os.makedirs(os.path.dirname(LogsUsagePath), exist_ok=True)
            with open(LogsUsagePath, "w") as stream:
                stream.write(json.dumps(self.measurements))

            return out
        return Measurement

    def __getConfig(self):
        with open('config/config.yaml') as yaml_data_file:
            self.config = yaml.load(yaml_data_file, Loader=yaml.FullLoader).get("Mail")

    @__usageMeasurement
    def __getDomainsList(self):
        url = self.config.get("ApiUrl") + "/request/domains/"

        headers = {
            'x-rapidapi-host': self.config.get("ApiHost"),
            'x-rapidapi-key': self.config.get("ApiKey")
            }

        response = requests.request("GET", url, headers=headers)

        logging.info(f"Response : {response.status_code}, {response.text}")

        domains_list = list(set(ast.literal_eval(response.text)) & set(self.config.get("TestedDomain")))
        if domains_list == [] or domains_list is None:
            logging.error(f"No domain found and tested. falling back to non tested domains\n From Api : {response.text}, tested domains : {self.config.get('TestedDomain')}")
            domains_list = list(set(ast.literal_eval(response.text)))

        self.domains = {"domains_list": domains_list,
                        "last_checked": datetime.now()}

        return "Domain"

    def GetRandomMailAddress(self):
        random_name = names.get_full_name().replace(" ", "_")

        self.__checkDomains()
        mail_address = str(random_name + random.choice(self.domains["domains_list"])).lower()

        if hasattr(self, "managed_address"):
            self.managed_address.append({"mail_address":mail_address, "created": datetime.now()})
        else:
            self.managed_address = [{"mail_address":mail_address, "created": datetime.now()}]

        logging.info(f"Mail address created : {mail_address}") 
        logging.info(f"Managed address : {list(map(lambda x:x.get('mail_address'), self.managed_address))}")
        self.__purgeManagedAddress()
        return mail_address

    def __checkDomains(self):
        """
        Check if domains have been retrieved and if they are not too old
        """
        if hasattr(self, "domains"):
            if "last_checked" in self.domains and (datetime.now() - self.domains.get("last_checked")).total_seconds() < self.config.get("DomainRenewalTime"):
                return True
    
        self.__getDomainsList()
        return True

    @__usageMeasurement
    def __GetMailsFromInbox(self, mail_address):

        url = self.config.get("ApiUrl") + f"/request/mail/id/{hashlib.md5(mail_address.encode()).hexdigest()}/"

        headers = {
            'x-rapidapi-host': self.config.get("ApiHost"),
            'x-rapidapi-key': self.config.get("ApiKey")
            }

        response = requests.request("GET", url, headers=headers)

        try :
            index = list(map(lambda x: x.get("mail_address"), self.managed_address)).index(mail_address)
            self.managed_address[index].update({"mails": ast.literal_eval(response.text)})
        except ValueError:
            self.managed_address.append({"mail_address":mail_address, "mails": ast.literal_eval(response.text)})

        logging.info(f'Get mails : {url} from : {mail_address} Response : {response.status_code}, number of message : {len(ast.literal_eval(response.text)) if type(ast.literal_eval(response.text)) is list else 0}')

        return "GetMails"

    def WaitForMail(self, mail_address, max_retry = 3):
        max_retry = self.config.get("MaxRetry", max_retry)
        retry = 0
        last_mail = self.GetLastMail(mail_address)
        while last_mail is None:
            if retry >= max_retry:
                break
            time.sleep(self.config.get('GetMailRetryTime'))
            last_mail = self.GetLastMail(mail_address)
            retry += 1
        if last_mail is None:
            raise TimeoutError("No email found in inbox")
        self.ApproveDomain(mail_address)
        return last_mail
    
    def _RemoveDuplicates(self, list_to_check):
        return list(set(list_to_check))

    def ApproveDomain(self, mail_address):
        """Add domain to tested domain list and write it to config file

        Args:
            mail_address (string): mail address to approve
        """
        domain = "@" + mail_address.split("@")[1]
        if domain not in self.config.get("TestedDomain"):

            with open('config/config.yaml') as yaml_data_file:
                full_config = yaml.load(yaml_data_file, Loader=yaml.FullLoader)

            full_config.get("Mail").get("TestedDomain").append(domain)
            full_config["Mail"]["TestedDomain"] = self._RemoveDuplicates(
                full_config.get("Mail").get("TestedDomain"))
            with open('config/config.yaml', 'w') as yaml_data_file:
                yaml.dump({"Mail": self.config}, yaml_data_file)
            self.__getDomainsList()
            logging.info(f"Domain approved : {domain}")

    def GetLastMail(self, mail_address):
        """Get last mail from an inbox

        Args:
            mail_address (str): mail adress to check last mail

        Returns:
            dict: mail returned by api
        """

        self.__GetMailsFromInbox(mail_address)

        index = list(map(lambda x: x.get("mail_address"), self.managed_address)).index(mail_address)
        if type(self.managed_address[index].get("mails")) is dict and len(list(self.managed_address[index].get("mails").keys())) == 1:
            # No mail in box
            logging.error("No mail in inbox")
            return None
        elif type(self.managed_address[index].get("mails")) is list:
            logging.debug(f"mail returned : {self.managed_address[index].get('mails')[-1]}")
            return self.managed_address[index].get("mails")[-1]

    def HtmlFromMail(self, mail):
        try:
            html = mail.get("mail_html")
        except AttributeError:
            raise AttributeError("Invalid mail to parse")
        return html

    def __purgeManagedAddress(self):
        for index, address in enumerate(self.managed_address):
            if hasattr(address, "created") and (datetime.now() - address.get("created")).total_seconds() > self.config.get("AddressHandlingTime"):
                
                if self.config.get("DeleteMailOnDrop") and hasattr(address, "mails"):
                    for mail in address.get("mails"):
                        try:
                            mail_id = mail.get("mail_id")
                            self.__deleteMail(mail_id)
                        except AttributeError:
                            logging.info("No mail to delete")
                
                self.managed_address.remove(address)

            if not "created" in address:
                logging.error(f"{address.get('mail_address')} has no creation time")
                self.managed_address[index]["created"] = datetime.now()

    @__usageMeasurement
    def __deleteMail(self, mail_id):
        url = self.config.get("ApiUrl") + f"/request/delete/id/{mail_id}/"

        headers = {
            'x-rapidapi-host': self.config.get("ApiHost"),
            'x-rapidapi-key': self.config.get("ApiKey")
            }

        response = requests.request("GET", url, headers=headers)

        logging.info(f"Response : {response.status_code}, {response.text}")

        return "Deleted"