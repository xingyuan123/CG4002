import crc8
from colorama import Fore

from Settings.Constants import FRAGMENTED_PACKETS, BYTES_RECEIVED, DURATION


def calculate_crc(data):
    crc = crc8.crc8()
    crc.update(data)
    return int.from_bytes(crc.digest(), byteorder='big')


def calculate_transmission_speed(device_id):
    if DURATION[device_id] == 0:
        return 0
    else:
        kilobits_received = BYTES_RECEIVED[device_id] * 8 / 1000
        return kilobits_received / DURATION[device_id]


def get_signed_int(first_byte, second_byte):
    val = (first_byte << 8) | second_byte
    if (val & (1 << 15)) != 0:
        val = val - (1 << 16)
    return val


def int_to_bytes(integer):
    return int.to_bytes(integer, 1, byteorder='big')


def checksum_fail(data):
    return data[-1] != calculate_crc(data[:-1])


def send_hello(characteristic):
    hello_packet = b'H' + b'\x00' * 18
    crc = calculate_crc(hello_packet)
    hello_packet += bytes([crc])
    characteristic.write(hello_packet)


def send_acknowledgement(characteristic):
    ack_packet = b'A' + b'\x00' * 18
    crc = calculate_crc(ack_packet)
    ack_packet += bytes([crc])
    characteristic.write(ack_packet)


def send_proceed(characteristic):
    proc_packet = b'P' + b'\x00' * 18
    crc = calculate_crc(proc_packet)
    proc_packet += bytes([crc])
    characteristic.write(proc_packet)


def print_summary(device_id, color, error):
    print(
        color +
        '================SUMMARY================\n' +
        f'<Device {device_id}> {error}\n' +
        f'<Device {device_id}> Transmission Speed: {calculate_transmission_speed(device_id):.2f}kbps\n' +
        f'<Device {device_id}> Fragmented Packets: {FRAGMENTED_PACKETS[device_id]}\n' +
        '=======================================' +
        Fore.RESET
    )


def reset_global_arrays(device_id):
    FRAGMENTED_PACKETS[device_id] = 0
    BYTES_RECEIVED[device_id] = 0
    DURATION[device_id] = 0.0
