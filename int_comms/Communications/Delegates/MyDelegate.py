from bluepy.btle import DefaultDelegate
from colorama import Fore

from Settings.Config import CHECKSUM_FAIL_THRESHOLD
from Settings.Constants import BYTES_RECEIVED, FRAGMENTED_PACKETS, PACKET_SIZE
from Utils import send_acknowledgement, send_hello, checksum_fail


class MyDelegate(DefaultDelegate):
    def __init__(self, characteristic, device_id, color, data_in, data_out):
        DefaultDelegate.__init__(self)
        self.characteristic = characteristic
        self.device_id = device_id
        self.color = color
        self.data_in = data_in
        self.data_out = data_out
        self.handshake_completed = False
        self.buffer = b''
        self.consecutive_checksum_fail_count = 0

    def handleNotification(self, c_handle, data):
        BYTES_RECEIVED[self.device_id] += len(data)
        self.update_buffer(data)

    def update_buffer(self, data):
        self.buffer += data
        if len(self.buffer) >= PACKET_SIZE:
            packet_data = self.buffer[:PACKET_SIZE]
            self.buffer = self.buffer[PACKET_SIZE:]
            self.process_packet(packet_data)
        else:
            FRAGMENTED_PACKETS[self.device_id] += 1

    def process_packet(self, packet_data):
        if checksum_fail(packet_data):
            self.handle_checksum_fail()
        else:
            self.consecutive_checksum_fail_count = 0
            packet_id = chr(packet_data[0])
            if not self.handshake_completed and packet_id == 'A':
                self.complete_handshake()
            elif packet_id == 'D':
                self.handle_data(packet_data)

    def handle_checksum_fail(self):
        self.consecutive_checksum_fail_count += 1
        print(self.color + f'<Device {self.device_id}> Failed checksum, discarded packet.' + Fore.RESET)
        if self.consecutive_checksum_fail_count == CHECKSUM_FAIL_THRESHOLD:
            print(self.color + f'<Device {self.device_id}> Failed checksum 3 consecutive times 🙁' + Fore.RESET)
            self.initialize_handshake()

    def initialize_handshake(self):
        self.reset()
        send_hello(self.characteristic)
        print(self.color + f'<Device {self.device_id}> Initialized handshake.' + Fore.RESET)

    def complete_handshake(self):
        send_acknowledgement(self.characteristic)
        self.handshake_completed = True
        self.data_out.put(str([self.device_id, 'C']))
        print(self.color + f'<Device {self.device_id}> Completed handshake, sent acknowledgement packet 🙂' + Fore.RESET)

    def handle_data(self, packet_data):
        print(self.color + f'<Device {self.device_id}> Override me!')

    def handle_server_data(self, server_data):
        print(self.color + f'<Device {self.device_id}> Override me!')

    def reset(self):
        self.buffer = b''
        self.consecutive_checksum_fail_count = 0
        self.handshake_completed = False
