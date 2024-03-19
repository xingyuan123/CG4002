import socket
import json
from queue import Queue
from threading import Thread, Event
from time import perf_counter
from Helper import MsgHelper, ice_print_e as print

conn = socket.socket()

class EvalClient: 
    def __init__(self, num_players, msg: MsgHelper, port): 
        self.num_players = num_players
        self.msg = msg
        self.sent     = Event()
        self.received = Event()

        # connect to eval server
        SERVER = 'localhost' 
        PORT = port 
        ADDR = (SERVER, PORT)
        conn.connect(ADDR)
        print('Client connected')
        
        # send hello packet to verify password
        conn.send(msg.format_text('hello', encrypted=True))

    # def send_and_recv(self, player_info, recv_q: Queue):
    #     # send player info (id, action, game state)
    #     conn.send(self.msg.format_text(json.dumps(player_info), encrypted=True))

    #     # recv correct game state
    #     self.success, recv = self.msg.recv_text(conn) 
    #     if self.success:
    #         print(f'Receive data: {recv}')
    #         recv_q.put(json.loads(recv))

    def send(self, eval_out: Queue):
        while True:
            for _ in range(self.num_players):
                # send player info (id, action, game state)
                player_info = eval_out.get()
                print(f'Sending data: {player_info}')
                conn.send(self.msg.format_text(json.dumps(player_info), encrypted=True))
            self.sent.set()
    
    def recv(self, eval_in: Queue):
        while True:
            for _ in range(self.num_players):
                # recv correct game state
                self.success, recv = self.msg.recv_text(conn) 
                if self.success:
                    print(f'Receive data: {recv}')
                    eval_in.put(json.loads(recv))
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
            self.sent.clear()
            self.received.clear()
            round_end.set()
        
            # start_time = perf_counter()
            # for _ in range(self.num_players):
            #     player_info = eval_out.get()
            #     print(f'Sending data: {player_info}')
            #     send_and_recv = Thread(target=self.send_and_recv, args=(player_info, eval_in,))
            #     send_and_recv.start()
            #     send_and_recv.join(timeout = 100)  # CURRENTLY SET TO OVER 1 MIN!!!!!!!!!!!!!!!!!! 
            # print(f'Server response time: {perf_counter()-start_time}')
            # round_end.set()