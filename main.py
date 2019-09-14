import serial
import pyudev
import usb.core
import logging
import config as cfg
from enum import Enum


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
                    self.on_detection()


class Status(Enum):
    NORMAL = 0
    ALARM = 1
    NO_SENSOR = 2


class PLDS:

    POWER_OUTAGE_MESSAGE = "POWEROUTAGE"
    POWER_BACK_MESSAGE = "POWERBACK"
    MAX_MESSAGE_LENGTH = 1000
    SER_DEVICE = "/dev/ttyACM0"
    BAUD_RATE = 9600
    ARDUINO_VENDOR_ID = 9025

    def __init__(self):
        self.status: Status = Status.NO_SENSOR
        self.ser = None

    def on_power_outage(self):
        if self.status is not Status.ALARM:
            self.status = Status.ALARM
            print('POWER OUTAGE')
        pass

    def on_power_back(self):
        if self.status is not Status.NORMAL:
            self.status = Status.NORMAL
            print('POWER BACK')
        pass

    def wait_for_data(self):
        if self.status is not Status.NO_SENSOR:
            try:
                while True:
                    data = str(self.ser.readline(1000))
                    if PLDS.POWER_OUTAGE_MESSAGE in data:
                        self.on_power_outage()
                    elif PLDS.POWER_BACK_MESSAGE in data:
                        self.on_power_back()
            except serial.SerialException:
                self.on_connection_lost()
        else:
            self.wait_for_sensor()

    def on_connection_lost(self):
        print('DISCONNECTED')
        self.status = Status.NO_SENSOR
        self.ser.close()
        self.wait_for_sensor()

    def try_connection(self):
        try:
            self.ser = serial.Serial(PLDS.SER_DEVICE, PLDS.BAUD_RATE)
            self.status = Status.NORMAL
            self.wait_for_data()
        except serial.SerialException:
            self.wait_for_sensor()

    def wait_for_sensor(self):
        detector = USBDetector(PLDS.ARDUINO_VENDOR_ID, self.try_connection)
        detector.listen()

    def start(self):
        self.try_connection()


if __name__ == "__main__":
    logging.basicConfig(filename=cfg.log_file, level=cfg.log_level, filemode='a+', format='%(asctime)s - %(levelname)s:: %(message)s')
    logging.debug('PLDS started.')
    plds = PLDS()
    plds.start()

