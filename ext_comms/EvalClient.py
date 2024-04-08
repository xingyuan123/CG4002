import socket
import json
from queue import Queue
from threading import Thread, Event
from Helper import MsgHelper, ice_print_e as print

conn = socket.socket()

class EvalClient: 
    def __init__(self, num_players, msg: MsgHelper): 
        self.num_rounds  = 0
        self.num_players = num_players
        self.msg         = msg
        self.sent        = Event()
        self.received    = Event()
    
    def start(self):
        # connect to eval server
        SERVER = 'localhost' 
        # PORT = 8888 
        print('Enter Port: ')
        PORT = int(input())
        ADDR = (SERVER, PORT)

        conn.connect(ADDR)
        print('Client connected')
        # send hello packet to verify password
        conn.send(self.msg.format_text('hello', encrypted=True))

    def send(self, eval_out: Queue):
        attempts = 3
        while True:
            player_info = [None for _ in range(self.num_players)]
            self.received.clear()
            for _ in range(attempts):
                for i in range(self.num_players):
                    # get player info (id, action, game state)
                    if player_info[i] == None:
                        player_info[i] = eval_out.get()
                    print(f'Sending data: {player_info[i]}')
                    conn.send(self.msg.format_text(json.dumps(player_info[i]), encrypted=True))
                self.sent.set()
                received = self.received.wait(timeout=16)
                # retry if not received
                if received: break

    def recv(self, eval_in: Queue):
        while True:
            for _ in range(self.num_players):
                # recv correct game state
                self.success, recv = self.msg.recv_text(conn) 
                if self.success:
                    print(f'Receive data: {recv}')
                    eval_in.put(json.loads(recv))
            self.num_rounds += 1
            self.received.set()
            
    def conn_eval_server(self, eval_out: Queue, eval_in: Queue, round_end: Event):
        send_thread = Thread(target=self.send, args=(eval_out,))
        recv_thread = Thread(target=self.recv, args=(eval_in,))

        send_thread.start()
        recv_thread.start()

        while True:
            self.sent.wait()
            self.received.wait()
            print('Sent and received')
            round_end.set()
            self.sent.clear()
            self.received.clear()
        