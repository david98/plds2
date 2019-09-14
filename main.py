import serial
import pyudev
import usb.core
import logging
import config as cfg
from enum import Enum
import time


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


class Status(Enum):
    NORMAL = 0
    ALARM = 1
    NO_SENSOR = 2


class PLDS:

    def __init__(self):
        self.status: Status = Status.NO_SENSOR
        self.ser = None

    def on_power_outage(self):
        if self.status is not Status.ALARM:
            self.status = Status.ALARM
            logging.warning('Power outage detected.')
        pass

    def on_power_back(self):
        if self.status is not Status.NORMAL:
            self.status = Status.NORMAL
            logging.warning('Power came back.')
        pass

    def on_connection_lost(self):
        logging.error('Sensor disconnected.')
        self.status = Status.NO_SENSOR
        self.ser.close()
        self.wait_for_sensor()

    def wait_for_data(self):
        if self.status is not Status.NO_SENSOR:
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
            self.status = Status.NORMAL
            logging.info('Connection to sensor established.')
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


if __name__ == "__main__":
    logging.basicConfig(filename=cfg.log_file, level=cfg.log_level, filemode='a+',
                        format='%(asctime)s - %(levelname)s:: %(message)s')
    logging.info('PLDS started.')
    plds = PLDS()
    plds.start()

