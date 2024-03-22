import asyncio
import socket
import ast
from pandas import DataFrame
from queue import Queue
from Helper import MsgHelper, ice_print_d as print, ice_print_x as alert
from threading import Event

def format_game_state(gs):
    return [
        gs['p1']['hp'], 
        gs['p1']['bullets'], 
        gs['p1']['shield_hp'], 
        gs['p2']['hp'], 
        gs['p2']['bullets'], 
        gs['p2']['shield_hp']
    ]

class DataServer:
    """
    Class that communicates with 
    - DataClient on relay laptop
    - AI on Ultra96
    """

    DEVICE_IDS = {
        1: ('VEST',  1), 
        2: ('GLOVE', 1), 
        3: ('GUN',   1), 
        4: ('VEST',  2), 
        5: ('GLOVE', 2), 
        6: ('GUN',   2)
    }
    
    def __init__(self, msg: MsgHelper):
        self.msg = msg

        self.is_running     = True
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # TCP socket connecting to the data client
        self.socket.bind(("", 0))
        self.port_number = self.socket.getsockname()[1]
        print('Waiting for client connection on port ' + str(self.port_number))

        self.addr   = None  # address of the client
        self.conn   = None  # address of the client socket

    async def accept (self):
        """
        Asynchronously wait for a single client to connect
        """
        if not self.is_running:
            return
        self.socket.listen(1)
        self.socket.setblocking(False)

        loop = asyncio.get_event_loop()
        self.conn, self.addr = await loop.sock_accept(self.socket)
        print('Client connected')

    async def recv_data(self, action_done, is_shot, ai_done: Event, connect, ai_q: Queue, eng_q: Queue):
        self.conn.setblocking(True)
        while True:
            ai_done.wait()
            try:
                _, data = self.msg.recv_text(self.conn)
            except:
                # If data client disconnects, reconnect on the same port
                print(f"Client disconnected. Waiting for reconn on {self.port_number}")
                await self.accept()
                self.conn.setblocking(True)
                continue
            data = ast.literal_eval(data)
            device_id = data[0]
            device, player_id = self.DEVICE_IDS[device_id]
            print(f'Player: {player_id}, Device: {device}')

            # handle disconnect packets
            if data[1] == 'D':
                connect[device_id].clear()
                connect[0].clear()
                alert(f'PLAYER {player_id} {device} DISCONNECTED')
                continue
            if data[1] == 'C':
                connect[device_id].set()
                alert(f'PLAYER {player_id} {device} CONNECTED')
                reconnected = True
                for item in connect[1:]:
                    if not item.is_set():
                        alert(f'DEVICES STILL DISCONNECTED')
                        reconnected = False
                        break
                # no devices disconnected
                if reconnected:
                    alert('All devices connected! :)')
                    connect[0].set()
                continue

            if device == 'VEST':
                (health, shield) = data[1:]
                print(f'P{player_id} hp: {health}, shield hp: {shield}')
                is_shot[player_id].set()
                continue

            # if player has already done action, do not process
            if action_done[player_id].is_set():
                print(f'Player {player_id} has already done action. Skipping...')
                continue

            if device == 'GLOVE':
                sensor_data = DataFrame(data[1])
                print(f'P{player_id} glove data:\n{sensor_data}')
                ai_q.put([sensor_data, player_id])
            elif device == 'GUN':
                bullets = data[1]
                print(f'P{player_id} bullets: {bullets}')
                eng_q.put(['gun', player_id])

    def recv_data_p(self, action_done, is_shot, ai_done: Event, connect, ai_q: Queue, eng_q: Queue):
        asyncio.run(self.recv_data(action_done, is_shot, ai_done, connect, ai_q, eng_q))

    def send_data(self, queue: Queue):
        while True:
            data = queue.get()
            data = format_game_state(data)
            print(f'Sending {data}') 
            data = self.msg.format_text(str(data))
            self.conn.send(data)

