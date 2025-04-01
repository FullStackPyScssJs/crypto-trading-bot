import logging
import requests

class NotificationManager:
    def __init__(self, notification_settings):
        """
        Initializes the NotificationManager with configuration parameters.

        Args:
            notification_settings (dict): The bot's configuration including notification settings.
        """
        self.notif_settings = notification_settings
        self.telegram_bot_token = notification_settings.get("notifications", {}).get("telegram", {}).get("bot_token")
        self.telegram_chat_id = notification_settings.get("notifications", {}).get("telegram", {}).get("chat_id")

    def send_telegram_message(self, message):
        """
        Sends a message via Telegram.

        Args:
            message (str): The message to send.
        """
        if not self.telegram_bot_token or not self.telegram_chat_id:
            logging.warning("Telegram configuration is missing.")
            return

        url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
        payload = {
            "chat_id": self.telegram_chat_id,
            "text": message
        }
        try:
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                logging.info("Telegram message sent successfully.")
            else:
                logging.error(f"Failed to send Telegram message: {response.text}")
        except Exception as e:
            logging.error(f"Error sending Telegram message: {e}")

    def log_and_notify(self, message):
        """
        Logs a message and sends it as a notification if configured.

        Args:
            message (str): The message to log and notify.
        """
        logging.info(message)
        self.send_telegram_message(message)

if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    # Example configuration
    notif_settings = {
        "notifications": {
            "telegram": {
                "bot_token": "your_telegram_bot_token",
                "chat_id": "your_telegram_chat_id"
            }
        }
    }

    notifier = NotificationManager(notif_settings)

    # Test sending a message
    notifier.log_and_notify("Test message from the Crypto Trading Bot!")
