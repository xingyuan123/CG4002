import base64
import os
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad


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
        text_received = ""
        success = False

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
                    raise Exception
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
                    raise Exception
                msg = data.decode("utf8")  # Decode raw bytes to UTF-8
                if not encrypted:
                    return True, msg
                text_received = self.decrypt_message(msg)
                success = True
                break
        except ConnectionResetError:
            raise Exception

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
            print("<Server> Exception in decrypt_message: ", e)
        return decrypted_message
