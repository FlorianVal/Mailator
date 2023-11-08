import unittest
from unittest.mock import mock_open, patch, MagicMock

from utils.notifications import NotificationManager

class MockRequest:
    remote_addr = '123.123.123.123'
    user_agent = MagicMock(string='MockAgent/1.0')

class TestNotificationManager(unittest.TestCase):

    def setUp(self):
        self.mock_request = MockRequest()

    @patch("requests.post")
    def test_send_notification(self, mock_post):
        with patch(
            "builtins.open",
            mock_open(
                read_data="""
                Notifications:
                    notifications_enabled: true
                    NtfyUrl: 'http://ntfy.sh'
                    NtfyTopic: 'test_topic_push_v111'
                    AppName: 'Test App send notification'
                """
            ),
        ):
            # Setup the singleton instance
            manager = NotificationManager.getInstance(reload_config=True)
            # Test sending a notification
            manager.send_notification("Test message mocked")
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            self.assertIn("http://ntfy.sh/test_topic_push_v111", call_args[0][0])
            self.assertIn("message", call_args[1]["data"])
            self.assertEqual(call_args[1]["data"], "Test message mocked")

    def test_singleton_behavior(self):
        manager1 = NotificationManager.getInstance()
        manager2 = NotificationManager.getInstance()
        self.assertEqual(manager1, manager2)

    @patch("requests.post")
    def test_no_notification_sent_when_disabled(self, mock_post):
        with patch(
            "builtins.open",
            mock_open(
                read_data="""
                Notifications:
                    notifications_enabled: false
                    NtfyUrl: 'http://ntfy.sh'
                    NtfyTopic: 'test_topic_push_v111'
                """
            ),
        ):
            manager = NotificationManager.getInstance(reload_config=True)

            manager.send_notification("Test message")
            mock_post.assert_not_called()

    def test_no_patch_notification(self):
        with patch(
            "builtins.open",
            mock_open(
                read_data="""
                Notifications:
                    notifications_enabled: true
                    NtfyUrl: 'http://ntfy.sh'
                    NtfyTopic: 'test_topic_push_v111'
                """
            ),
        ):
            manager = NotificationManager.getInstance(reload_config=True)
            manager.send_notification("Test message")

    @patch("requests.post")
    def test_error_missing_argument(self, mock_post):
        with patch(
            "builtins.open",
            mock_open(
                # Missing NtfyUrl
                read_data="""
                Notifications:
                    notifications_enabled: true
                    NtfyTopic: 'test_topic_push_v111'
                """
            ),
        ):
            with self.assertRaises(ValueError):
                manager = NotificationManager.getInstance(reload_config=True)
                manager.send_notification("Missing argument message")
            mock_post.assert_not_called()

    @patch("requests.post")
    def test_error_missing_argument_not_enabled(self, mock_post):
        """
        If notifications are not enabled, no error should be raised when missing arguments
        """
        with patch(
            "builtins.open",
            mock_open(
                # Missing NtfyUrl
                read_data="""
                Notifications:
                    notifications_enabled: false
                    NtfyTopic: 'test_topic_push_v111'
                """
            ),
        ):
            manager = NotificationManager.getInstance(reload_config=True)
            manager.send_notification(
                "Missing argument message but message not enabled"
            )
            mock_post.assert_not_called()

    @patch("requests.post")
    def test_send_notification_with_user_logging_enabled(self, mock_post):
        config_data = """
        Notifications:
          notifications_enabled: true
          log_user: true
          NtfyUrl: 'http://ntfy.sh'
          NtfyTopic: 'test_topic'
        """
        with patch('builtins.open', mock_open(read_data=config_data)):
            manager = NotificationManager.getInstance(reload_config=True)
            manager.send_notification("Route called", self.mock_request)
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            expected_message = "Route called from IP 123.123.123.123 using MockAgent/1.0"
            self.assertIn(expected_message, call_args[1]["data"])

    @patch("requests.post")
    def test_send_notification_with_user_logging_disabled(self, mock_post):
        config_data = """
        Notifications:
          notifications_enabled: true
          log_user: false
          NtfyUrl: 'http://ntfy.sh'
          NtfyTopic: 'test_topic'
        """
        with patch('builtins.open', mock_open(read_data=config_data)):
            manager = NotificationManager.getInstance(reload_config=True)
            manager.send_notification("Route called", self.mock_request)
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            self.assertEqual("Route called", call_args[1]["data"])


# Run the tests
if __name__ == "__main__":
    unittest.main()
