import unittest
from unittest.mock import mock_open, patch

from utils.notifications import NotificationManager


class TestNotificationManager(unittest.TestCase):
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
                manager.send_notification()
            mock_post.assert_not_called()

# Run the tests
if __name__ == "__main__":
    unittest.main()
