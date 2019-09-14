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