import time

from bluepy.btle import Peripheral
from colorama import Fore

from Delegates.GloveDelegate import GloveDelegate
from Delegates.GunDelegate import GunDelegate
from Delegates.VestDelegate import VestDelegate
from Settings.Config import HANDSHAKE_TIMEOUT
from Settings.Constants import SERVICE_UUID, CHARACTERISTIC_UUID, DEVICE_IDS, DURATION
from Utils import send_hello, print_summary, reset_global_arrays


def beetle_process(mac, device_id, color, data_in, data_out):
    while True:
        try:
            beetle = Beetle(mac, device_id, color, data_in, data_out)
            handle_beetle(beetle)
        except Exception as e:
            print(color + f'<Device {device_id}> {e} 🥒' + Fore.RESET)
            data_out.put(str([device_id, 'D']))


def handle_beetle(beetle):
    prev_time = beetle.start_time
    while True:
        DURATION[beetle.device_id] = time.time() - beetle.start_time
        beetle.peripheral.waitForNotifications(1.0)
        curr_time = time.time()
        if not beetle.peripheral.delegate.handshake_completed:
            if curr_time - prev_time > HANDSHAKE_TIMEOUT:
                send_hello(beetle.characteristic)
                prev_time = curr_time
        check_server_data(beetle)


def check_server_data(beetle):
    if not beetle.data_in.empty():
        if beetle.peripheral.delegate.handshake_completed:
            beetle.peripheral.delegate.handle_server_data(beetle.data_in.get())


def set_delegate(peripheral, characteristic, device_id, color, data_in, data_out):
    if device_id == DEVICE_IDS['VEST_1'] or device_id == DEVICE_IDS['VEST_2']:
        peripheral.setDelegate(VestDelegate(characteristic, device_id, color, data_in, data_out))
    if device_id == DEVICE_IDS['GLOVE_1'] or device_id == DEVICE_IDS['GLOVE_2']:
        peripheral.setDelegate(GloveDelegate(characteristic, device_id, color, data_in, data_out))
    if device_id == DEVICE_IDS['GUN_1'] or device_id == DEVICE_IDS['GUN_2']:
        peripheral.setDelegate(GunDelegate(characteristic, device_id, color, data_in, data_out))


class Beetle:
    def __init__(self, mac, device_id, color, data_in, data_out):
        self.mac = mac
        self.device_id = device_id
        self.color = color
        self.data_in = data_in
        self.data_out = data_out
        self.peripheral = Peripheral()
        self.service = None
        self.characteristic = None
        self.start_time = time.time()
        self.setup()

    def setup(self):
        self.peripheral.connect(self.mac)
        self.service = self.peripheral.getServiceByUUID(SERVICE_UUID)
        self.characteristic = self.service.getCharacteristics(CHARACTERISTIC_UUID)[0]
        set_delegate(self.peripheral, self.characteristic, self.device_id, self.color, self.data_in, self.data_out)
        send_hello(self.characteristic)
