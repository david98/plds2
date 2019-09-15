import serial
import pyudev
import usb.core
import logging
import config as cfg
from enum import Enum
import time
from datetime import datetime

from telegram.ext import Updater, CommandHandler


class USBDetector:

    def __init__(self, vendor_id: int, on_detection):
        self.context = pyudev.Context()
        self.monitor = pyudev.Monitor.from_netlink(self.context)
        self.monitor.filter_by(subsystem='usb')
        self.vendor_id = vendor_id
        self.on_detection = on_detection

    def listen(self):
        for device in iter(self.monitor.poll, None):
            if device.action == 'add':
                dev = usb.core.find(idVendor=self.vendor_id)
                if dev is not None:
                    logging.debug('USB Detector: new USB device detected.')
                    self.on_detection()
            time.sleep(cfg.time_between_usb_checks)


class TelegramBot:

    def __init__(self, commands: list, executor):
        self.updater = Updater(token=cfg.telegram_bot_key, use_context=True)
        self.start_handler = CommandHandler('start', self.start)
        self.updater.dispatcher.add_handler(self.start_handler)
        for command in commands:
            setattr(self, f'{command}_handler', CommandHandler(command, getattr(executor, command)))
            self.updater.dispatcher.add_handler(getattr(self, f'{command}_handler'))
        self.updater.start_polling()

    def start(self, update, context):
        if update.message.from_user.username in cfg.allowed_usernames:
            context.bot.send_message(chat_id=update.message.chat_id, text="Hi there!")

    def send_notification(self, message: str):
        for chat_id in cfg.notification_chat_ids:
            self.updater.bot.send_message(chat_id, message)


class Status(Enum):
    NORMAL = 0
    ALARM = 1
    NO_SENSOR = 2

    def __str__(self):
        if self.value is 0:
            return 'No problem.'
        elif self.value is 1:
            return 'We have a bit of a problem (cit.): no power'
        elif self.value is 2:
            return 'Sensor is not connected...'


class PLDS:

    def __init__(self):
        self.current_status: Status = Status.NO_SENSOR
        self.ser = None
        self.telegram_bot = TelegramBot(['status'], self)
        self.version = '2.0.0'
        self.last_outage_time = None

    def status(self, update, context):
        if update.message.from_user.username in cfg.allowed_usernames:
            if self.current_status is Status.ALARM:
                pass
            elif self.current_status is Status.NORMAL:
                pass
            elif self.current_status is Status.NO_SENSOR:
                context.bot.send_message(chat_id=update.message.chat_id,
                                         text=f'PLDS version {self.version}: {str(self.current_status)}')

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
            now = datetime.now()
            logging.warning('Power came back. Outage duration: '
                            f'{(now - self.last_outage_time).strftime("%H:%M:%S")}')
            self.telegram_bot.send_notification('Power came back. Outage duration: '
                                                f'{(now - self.last_outage_time).strftime("%H:%M:%S")}')

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
                    data = str(self.ser.readline(cfg.max_message_length))
                    if cfg.power_outage_message in data:
                        self.on_power_outage()
                    elif cfg.power_back_message in data:
                        self.on_power_back()
            except serial.SerialException:
                self.on_connection_lost()
        else:
            self.wait_for_sensor()

    def try_connection(self):
        try:
            self.ser = serial.Serial(cfg.ser_device, cfg.baud_rate)
            self.current_status = Status.NORMAL
            logging.info('Connection to sensor established.')
            self.telegram_bot.send_notification('Connection to sensor established.')
            self.wait_for_data()
        except serial.SerialException:
            logging.debug('Connection failed, probably tried with the wrong device.')
            self.wait_for_sensor()

    def wait_for_sensor(self):
        logging.debug('Starting USB detector...')
        detector = USBDetector(cfg.arduino_vendor_id, self.try_connection)
        detector.listen()

    def start(self):
        self.try_connection()

    def stop(self):
        if self.ser is not None:
            self.ser.close()
        self.telegram_bot.updater.idle()


if __name__ == "__main__":
    logging.basicConfig(filename=cfg.log_file, level=cfg.log_level, filemode='a+',
                        format='%(asctime)s - %(levelname)s:: %(message)s')
    logging.info('PLDS started.')
    plds = PLDS()
    plds.start()

