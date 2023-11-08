import requests
import yaml


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
                or not all(
                    key in yaml_content.get("Notifications")
                    for key in self._required_config_keys
                )
            ):
                raise ValueError(
                    f"Invalid config file {self.config_path}. Missing keys {self._required_config_keys}"
                )
            return yaml_content.get("Notifications")

    def send_notification(self, message):
        if self.config.get("notifications_enabled", False):
            ntfy_url = self.config.get("NtfyUrl")
            topic = self.config.get("NtfyTopic")
            complete_url = f"{ntfy_url}/{topic}"
            requests.post(complete_url, data=message, timeout=5)