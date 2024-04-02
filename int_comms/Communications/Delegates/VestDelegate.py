import struct

from Delegates.MyDelegate import MyDelegate
from Utils import calculate_crc, int_to_bytes, send_proceed


class VestDelegate(MyDelegate):
    def __init__(self, characteristic, device_id, color, data_in, data_out):
        MyDelegate.__init__(self, characteristic, device_id, color, data_in, data_out)
        self.sequence_id = -1

    def handle_data(self, packet_data):  # Override
        sensor_reading = struct.unpack('c' + 'B' * 19, packet_data)
        if sensor_reading[2] != self.sequence_id:
            self.data_out.put(str([self.device_id]))
            self.sequence_id = sensor_reading[2]
        send_proceed(self.characteristic)

    def handle_server_data(self, server_data):  # Override
        data_packet = b'D' + int_to_bytes(self.device_id) + b'\x00' * 17
        crc = calculate_crc(data_packet)
        data_packet += bytes([crc])
        self.characteristic.write(data_packet)

    def reset(self):  # Override
        super().reset()
        self.sequence_id = -1
