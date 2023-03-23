import os
from dotenv import load_dotenv

load_dotenv()


class PLDSConfig:
    def __init__(self):
        self.log_level = os.getenv('PLDS_LOG_LEVEL', 'DEBUG')
        self.usb_check_period = int(os.getenv('PLDS_USB_CHECK_PERIOD', 5))
        self.power_outage_string = os.getenv('PLDS_POWER_OUTAGE_STRING', 'POWEROUTAGE')
        self.power_back_string = os.getenv('PLDS_POWER_BACK_STRING', 'POWERBACK')
        self.max_msg_length = int(os.getenv('PLDS_MAX_MSG_LENGTH', 1000))
        self.serial_device = os.getenv('PLDS_SERIAL_DEVICE', '/dev/ttyACM0')
        self.baud_rate = int(os.getenv('PLDS_BAUD_RATE', 9600))
        self.arduino_vendor_id = int(os.getenv('PLDS_ARDUINO_VENDOR_ID', 9025))
        self.telegram_bot_key = os.getenv('PLDS_TELEGRAM_BOT_KEY')
        self.allowed_usernames = os.getenv('PLDS_ALLOWED_USERNAMES').split(',')
        self.notification_chat_ids = os.getenv('PLDS_NOTIFICATION_CHAT_IDS').split(',')