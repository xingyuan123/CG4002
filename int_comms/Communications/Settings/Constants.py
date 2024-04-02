from colorama import Fore

SERVICE_UUID = '0000dfb0-0000-1000-8000-00805f9b34fb'
CHARACTERISTIC_UUID = '0000dfb1-0000-1000-8000-00805f9b34fb'
ULTRA_96_IP = '172.26.191.218'
EVAL_SERVER_PASSWORD = '1234567890123456'
WINDOW_SIZE = 10
PACKET_SIZE = 20
GLOVE_READING_INDICES = indices = [2, 4, 6, 8, 10, 12]  # Indices for accX, accY, accZ, gyroX, gyroY, gyroZ

DEVICE_ADDRESSES = {
    'VEST_1': '',
    'GLOVE_1': '0C:B2:B7:1E:49:AD',
    'GUN_1': '0C:B2:B7:1E:49:9E',
    'VEST_2': 'F4:B8:5E:42:6D:20',
    'GLOVE_2': '',
    'GUN_2': '',
}

DEVICE_IDS = {
    'VEST_1': 1,
    'GLOVE_1': 2,
    'GUN_1': 3,
    'VEST_2': 4,
    'GLOVE_2': 5,
    'GUN_2': 6,
}

DEVICE_COLORS = {
    'VEST_1': Fore.GREEN,
    'GLOVE_1': Fore.MAGENTA,
    'GUN_1': Fore.YELLOW,
    'VEST_2': Fore.LIGHTGREEN_EX,
    'GLOVE_2': Fore.LIGHTMAGENTA_EX,
    'GUN_2': Fore.LIGHTYELLOW_EX,
}

FRAGMENTED_PACKETS = [0] * 7
BYTES_RECEIVED = [0] * 7
DURATION = [0.0] * 7
