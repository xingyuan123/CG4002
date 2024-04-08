import base64
import os
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from threading import Event

logging = True

def ice_print_x(arg):
    arg = 'ALERT! {}'.format(arg)
    ice_print(arg, color=1)

def ice_print_a(arg):
    arg = '[ AI ] {}'.format(arg)
    ice_print(arg, color=8)

def ice_print_d(arg):
    arg = '[DATA] {}'.format(arg)
    ice_print(arg, color=6)

def ice_print_t(arg):
    arg = '[TIME] {}'.format(arg)
    ice_print(arg, color=11)

def ice_print_g(arg):
    if logging:
        arg = '[GAME] {}'.format(arg)
        ice_print(arg, color=2)

def ice_print_e(arg):
    if logging:
        arg = '[EVAL] {}'.format(arg)
        ice_print(arg, color=3)

def ice_print_m(arg):
    return
    if logging:
        arg = '[MQTT] {}'.format(arg)
        ice_print(arg, color=5)

def ice_print(*arg, color=0, end='\n'):
    # ANSI colors
    _c = (
        "\033[0m",   # End of color
        '\033[31m',  # red
        '\033[32m',  # green
        '\033[33m',  # orange
        '\033[34m',  # blue
        '\033[35m',  # purple
        '\033[36m',  # cyan
        '\033[91m',  # light red
        '\033[92m',  # light green
        '\033[93m',  # yellow
        '\033[94m',  # lightblue
        '\033[95m',  # pink
        '\033[96m',  # light cyan
        '\033[37m',  # light grey
        '\033[90m',  # darkgrey
    )

    if color == 0:
        for a in arg:
            print(a, end=' ')
    else:
        for a in arg:
            print(_c[color] + str(a) + _c[0], end=' ')
    print(end, end='')

class Player:
    def __init__(self, player_id):
        self.player_id   = player_id
        self.action_done = Event()
        self.is_shot     = Event()
        self.ai_done     = Event()
        self.ai_done.set()

class MsgHelper: 
    iv = os.urandom(16)

    def __init__(self, key):
        self.key = key

    def format_text(self, msg, encrypted=False):
        msg = msg.encode('utf-8')
        if encrypted:
            msg = pad(msg, AES.block_size)
            cipher = AES.new(self.key.encode('utf-8'), AES.MODE_CBC, self.iv)
            msg = base64.b64encode(self.iv + cipher.encrypt(msg))
        formatted_msg = str(len(msg)).encode('utf-8') + b'_' + msg
        return formatted_msg
    
    def recv_text(self, conn, encrypted=False):
        text_received   = ""
        success         = False

        try:
            while True:
                # recv length followed by '_' followed by cypher
                data = b''
                while not data.endswith(b'_'):
                    _d = conn.recv(1)
                    if not _d:
                        data = b''
                        break
                    data += _d
                if len(data) == 0:
                    raise Exception('recv_text: client disconnected')
                data = data.decode("utf-8")
                length = int(data[:-1])

                data = b''
                while len(data) < length:
                    _d = conn.recv(1)
                    if not _d:
                        data = b''
                        break
                    data += _d
                if len(data) == 0:
                    raise Exception('recv_text: client disconnected')
                msg = data.decode("utf8")  # Decode raw bytes to UTF-8'
                if not encrypted:
                    return True, msg
                text_received = self.decrypt_message(msg)
                success = True
                break
        except ConnectionResetError:
            raise Exception('recv_text: Connection Reset')

        return success, text_received 

    def decrypt_message(self, cipher_text):
        """
        This function decrypts the response message received from the Ultra96 using
        the secret encryption key/ password
        """
        try:
            decoded_message = base64.b64decode(cipher_text)  # Decode message from base64 to bytes
            iv = decoded_message[:AES.block_size]  # Get IV value
            secret_key = bytes(str(self.key), encoding="utf8")  # Convert secret key to bytes

            cipher = AES.new(secret_key, AES.MODE_CBC, iv)  # Create new AES cipher object

            decrypted_message = cipher.decrypt(decoded_message[AES.block_size:])  # Perform decryption
            decrypted_message = unpad(decrypted_message, AES.block_size)
            decrypted_message = decrypted_message.decode('utf8')  # Decode bytes into utf-8
        except Exception as e:
            decrypted_message = ""
            print('exception in decrypt_message: ', e)
        return decrypted_message
    