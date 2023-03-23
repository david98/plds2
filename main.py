import os

import serial
import pyudev
import usb.core
import logging
from enum import Enum
import time
from datetime import datetime

from telegram.ext import Updater, CommandHandler

from config import PLDSConfig


class USBDetector:

    def __init__(self, vendor_id: int, on_detection, check_period: int):
        self.context = pyudev.Context()
        self.monitor = pyudev.Monitor.from_netlink(self.context)
        self.monitor.filter_by(subsystem='usb')
        self.vendor_id = vendor_id
        self.on_detection = on_detection
        self.check_period = check_period

    def listen(self):
        for device in iter(self.monitor.poll, None):
            if device.action == 'add':
                dev = usb.core.find(idVendor=self.vendor_id)
                if dev is not None:
                    logging.debug('USB Detector: new USB device detected.')
                    self.on_detection()
            time.sleep(self.check_period)


class TelegramBot:

    def __init__(self, commands: list, executor, bot_key: str,
                 allowed_usernames: [str], notification_chat_ids: [str]):
        self.allowed_usernames = allowed_usernames
        self.notification_chat_ids = notification_chat_ids
        self.updater = Updater(token=bot_key, use_context=True)
        self.start_handler = CommandHandler('start', self.start)
        self.updater.dispatcher.add_handler(self.start_handler)
        for command in commands:
            setattr(self, f'{command}_handler', CommandHandler(command, getattr(executor, command)))
            self.updater.dispatcher.add_handler(getattr(self, f'{command}_handler'))
        self.updater.start_polling()

    def start(self, update, context):
        if update.message.from_user.username in self.allowed_usernames:
            context.bot.send_message(chat_id=update.message.chat_id, text="Hi there!")

    def send_notification(self, message: str):
        for chat_id in self.notification_chat_ids:
            self.updater.bot.send_message(chat_id, message)


class Status(Enum):
    NORMAL = 0
    ALARM = 1
    NO_SENSOR = 2

    def __str__(self):
        if self.value == 0:
            return 'No problem.'
        elif self.value == 1:
            return 'We have a bit of a problem (cit.): no power'
        elif self.value == 2:
            return 'Sensor is not connected...'


class PLDS:

    def __init__(self, cfg: PLDSConfig):
        self.serial_device = cfg.serial_device
        self.baud_rate = cfg.baud_rate
        self.arduino_vendor_id = cfg.arduino_vendor_id
        self.max_msg_length = cfg.max_msg_length
        self.power_outage_string = cfg.power_outage_string
        self.power_back_string = cfg.power_back_string
        self.allowed_usernames = cfg.allowed_usernames
        self.current_status: Status = Status.NO_SENSOR
        self.ser = None
        self.telegram_bot = TelegramBot(['status'], self, allowed_usernames=cfg.allowed_usernames,
                                        notification_chat_ids=cfg.notification_chat_ids, bot_key=cfg.telegram_bot_key)
        self.version = '2.0.0'
        self.last_outage_time = None

    def status(self, update, context):
        if update.message.from_user.username in self.allowed_usernames:
            message = f'PLDS version {self.version}\n'
            if self.current_status is Status.ALARM:
                duration = datetime.now() - self.last_outage_time
                seconds = duration.total_seconds()
                hours = int(seconds // 3600)
                minutes = int((seconds % 3600) // 60)
                seconds = round(seconds % 60)
                message += f'Power has been down for {hours:02d}h:{minutes:02d}m:{seconds:02d}s'
            elif self.current_status is Status.NORMAL:
                message += 'No problem here.' if self.last_outage_time is None else \
                            f'No outage since {self.last_outage_time.strftime("%d/%m/%Y, %H:%M:%S")}'
            elif self.current_status is Status.NO_SENSOR:
                message += 'Sensor is currently disconnected.'

            context.bot.send_message(chat_id=update.message.chat_id,
                                     text=message)

    def on_power_outage(self):
        if self.current_status is not Status.ALARM:
            self.current_status = Status.ALARM
            self.last_outage_time = datetime.now()
            logging.warning('Power outage detected.')
            self.telegram_bot.send_notification('Power outage detected at '
                                                f'{self.last_outage_time.strftime("%d/%m/%Y, %H:%M:%S")}')

    def on_power_back(self):
        if self.current_status is not Status.NORMAL:
            self.current_status = Status.NORMAL
            duration = datetime.now() - self.last_outage_time
            seconds = duration.total_seconds()
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            seconds = round(seconds % 60)
            logging.warning(f'Power came back. Outage duration: {hours:02d}h:{minutes:02d}m:{seconds:02d}s')
            self.telegram_bot.send_notification('Power came back. Outage duration: '
                                                f'{hours:02d}h:{minutes:02d}m:{seconds:02d}s')

    def on_connection_lost(self):
        logging.error('Sensor disconnected.')
        self.telegram_bot.send_notification('Sensor disconnected.')
        self.current_status = Status.NO_SENSOR
        self.ser.close()
        self.wait_for_sensor()

    def wait_for_data(self):
        if self.current_status is not Status.NO_SENSOR:
            try:
                while True:
                    data = str(self.ser.readline(self.max_msg_length))
                    if self.power_outage_string in data:
                        self.on_power_outage()
                    elif self.power_back_string in data:
                        self.on_power_back()
            except serial.SerialException:
                self.on_connection_lost()
        else:
            self.wait_for_sensor()

    def try_connection(self):
        try:
            self.ser = serial.Serial(self.serial_device, self.baud_rate)
            self.current_status = Status.NORMAL
            logging.info('Connection to sensor established.')
            self.telegram_bot.send_notification('Connection to sensor established.')
            self.wait_for_data()
        except serial.SerialException:
            logging.debug('Connection failed, probably tried with the wrong device.')
            self.wait_for_sensor()

    def wait_for_sensor(self):
        logging.debug('Starting USB detector...')
        detector = USBDetector(self.arduino_vendor_id, self.try_connection, check_period=cfg.usb_check_period)
        detector.listen()

    def start(self):
        self.try_connection()

    def stop(self):
        if self.ser is not None:
            self.ser.close()
        self.telegram_bot.updater.idle()


if __name__ == "__main__":
    cfg = PLDSConfig()
    logging.basicConfig(level=cfg.log_level, format='%(asctime)s - %(levelname)s:: %(message)s')
    logging.info('PLDS started.')
    plds = PLDS(cfg=cfg)
    plds.start()

