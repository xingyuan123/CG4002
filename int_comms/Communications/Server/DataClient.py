import ast
import socket
from queue import Queue

from Server.MsgHelper import MsgHelper
from Settings.Constants import EVAL_SERVER_PASSWORD


class DataClient:
    def __init__(self, server_ip, server_port):
        self.server_ip = server_ip
        self.server_port = server_port
        self.conn = socket.socket()
        self.msg = MsgHelper(EVAL_SERVER_PASSWORD)
        self.ADDR = (server_ip, server_port)
        self.conn.connect(self.ADDR)

    def recv_data(self, queues):
        self.conn.setblocking(True)
        while True:
            _, data = self.msg.recv_text(self.conn)
            data = ast.literal_eval(data)
            for queue in queues:
                queue.put(data)
            print(f"<Server> Received data: {data}")

    def send_data(self, queue: Queue):
        while True:
            text = queue.get()
            print(f"<Server> Sent data: {text}")
            text = self.msg.format_text(text)
            self.conn.send(text)
