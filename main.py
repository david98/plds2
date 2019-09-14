import serial

POWER_OUTAGE_MESSAGE = "POWEROUTAGE"
POWER_BACK_MESSAGE = "POWERBACK"


def on_power_outage():
    print("ALARM!!!!")


def on_power_back():
    print("NOW OK!!!")


if __name__ == "__main__":
    ser = serial.Serial("/dev/ttyACM0", 9600, timeout=1)
    while True:
        data = str(ser.readline(1000))
        if POWER_OUTAGE_MESSAGE in data:
            on_power_outage()
        elif POWER_BACK_MESSAGE in data:
            on_power_back()
