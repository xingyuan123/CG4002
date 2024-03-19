import socket
import json
from Helper import MsgHelper, ice_print_e as print
from queue import Queue
from threading import Thread, Event
from time import perf_counter

conn = socket.socket()

class EvalClient: 
    def __init__(self, num_players, msg: MsgHelper, port): 
        self.num_players = num_players
        self.msg = msg

        # connect to eval server
        SERVER = 'localhost' 
        PORT = port 
        ADDR = (SERVER, PORT)
        conn.connect(ADDR)
        print('Client connected')

        # send hello packet to verify password
        conn.send(msg.format_text('hello', encrypted=True))

    def send_and_recv(self, player_info, recv_q: Queue):
        # send player info (id, action, game state)
        conn.send(self.msg.format_text(json.dumps(player_info), encrypted=True))

        # recv correct game state
        self.success, recv = self.msg.recv_text(conn) 
        if self.success:
            print(f'Receive data: {recv}')
            recv_q.put(json.loads(recv))

    def conn_eval_server(self, eval_out: Queue, eval_in: Queue, round_end: Event):
        while True:
            # self.success = False
            # tries = 4
            start_time = perf_counter()
            # send_and_recv = Thread(target=self.send_and_recv, args=(player_info, eval_in,))
            for _ in range(self.num_players):
                player_info = eval_out.get()
                print(f'Sending data: {player_info}')
                # send player info (id, action, game state)
                conn.send(self.msg.format_text(json.dumps(player_info), encrypted=True))

                # recv correct game state
                self.success, recv = self.msg.recv_text(conn) 
                if self.success:
                    print(f'Receive data: {recv}')
                    eval_in.put(json.loads(recv))
                    print(f'Server response time: {perf_counter()-start_time}')
                    round_end.set()
                else: 
                    print('Issue getting game state from eval server')
                # send_and_recv.start()
                # send_and_recv.join(timeout = 100)  # CURRENTLY SET TO OVER 1 MIN!!!!!!!!!!!!!!!!!! 
            
            # if self.success:
            
            # # send again if no response received in 14 seconds (max 4 tries)
            # # timeout for eval server is 60 seconds
            # while tries: 
            #     print(f'Tries left: {tries}')
            #     send_and_recv = Thread(target=self.send_and_recv, args=(player_info, eval_in,))
            #     send_and_recv.start()
            #     send_and_recv.join(timeout=10) 
            #     tries -= 1
            
            # eval server timed out, continue with existing game state
            # if not self.success:
            #     print('Eval server timed out')
            
            # round_end.set()
