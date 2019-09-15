# edit this then rename to config.py
from logging import DEBUG, INFO, WARNING, ERROR, CRITICAL
log_file = './plds.log'
log_level = DEBUG
time_between_usb_checks = 5
power_outage_message = "POWEROUTAGE"
power_back_message = "POWERBACK"
max_message_length = 1000
ser_device = "/dev/ttyACM0"
baud_rate = 9600
arduino_vendor_id = 9025
telegram_bot_key = 'YOUR_TELEGRAM_BOT_API_KEY'
allowed_usernames = ['a_username', 'another_username'] #only these users are allowed to send commands
notification_chat_ids =  ['12345678'] #these chats will receive notifications for events