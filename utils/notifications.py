import requests
import yaml
import logging


class NotificationManager:
    _instance = None
    _required_config_keys = ["notifications_enabled", "NtfyUrl", "NtfyTopic"]

    @staticmethod
    def getInstance(config_path="config/config.yaml", reload_config=False):
        if NotificationManager._instance is None:
            NotificationManager(config_path)
        if reload_config:
            NotificationManager._instance.config = (
                NotificationManager._instance.load_config()
            )
        return NotificationManager._instance

    def __init__(self, config_path="config/config.yaml"):
        if NotificationManager._instance is not None:
            raise Exception("This class is a singleton!")
        else:
            NotificationManager._instance = self
            self.config_path = config_path
            self.config = self.load_config()

    def load_config(self):
        with open(self.config_path, "r") as config_file:
            yaml_content = yaml.safe_load(config_file)
            if (
                "Notifications" not in yaml_content
                or yaml_content.get("Notifications") is None
                or "notifications_enabled" not in yaml_content.get("Notifications")
            ):
                raise ValueError(
                    f"Invalid config file {self.config_path}. Missing Notifications section or notifications_enabled key"
                )
            return yaml_content.get("Notifications")

    def send_notification(self, message, request=None):
        if self.config.get("notifications_enabled", False):
            if not all(key in self.config for key in ["NtfyUrl", "NtfyTopic"]):
                raise ValueError("Invalid config file: Missing 'NtfyUrl' or 'NtfyTopic' keys")

            # If log_user is enabled and the request object is provided, append details to message
            if self.config.get("log_user", False) and request:
                user_info = f" from IP {request.remote_addr} using {request.user_agent.string}"
                message += user_info

            ntfy_url = self.config.get("NtfyUrl")
            topic = self.config.get("NtfyTopic")
            complete_url = f"{ntfy_url}/{topic}"
            logging.info(f"Sending notification to {complete_url}")
            resp = requests.post(
                complete_url,
                data=message,
                headers={"Authorization": f"Bearer {self.config.get('NtfyToken', '')}"},
                timeout=5,
            )
            if resp.status_code != 200:
                logging.error(
                    f"Error sending notification to {complete_url}: {resp.status_code} - {resp.text}"
                )
