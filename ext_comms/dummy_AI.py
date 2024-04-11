from queue import Queue
from random import randint
from time import sleep
from threading import Thread
from Helper import Status, ice_print_a as print, ice_print_x as alert

# attacks, shield, reload or shoot
actions = ['bomb', 'captAmerica', 'hulk', 'idle', 'ironMan', 'logout', 'reload', 'shangChi', 'shield']

class Dummy_AI: 
    def gen_action(self, player_id, queue_in: Queue, queue_out: Queue):
        player = self.players[player_id]
        opponent = self.players[2] if player_id == 1 else self.players[1]
        print(f'AI thread for P{player_id} running')

        while True:
            data = queue_in.get()
            # wait for bitstream to become free
            opponent.ai_done.wait()
            # start processing own action
            player.ai_done.clear()
            print(f'Got\n{data}')
            sleep(3) # temp
            action = actions[randint(0, 8)]
            print(f'Generate {action} by player {player_id}')

            # handle idle action
            if action == 'idle':
                alert('Idle received. Try again')
            # stop early logout
            elif action == 'logout' and not self.end.is_set():
                alert('Logout received early. Try again')
            else:
                queue_out.put([action, player_id])
            player.ai_done.set()
    
    def run_ai(self, status: Status, queue_in: Queue, queue_out: Queue):
        self.end      = status.game_end
        self.players  = status.players

        p1_q = Queue()
        p1   = Thread(target=self.gen_action, args=(1, p1_q, queue_out))
        p1.start()

        p2_q = Queue()
        p2   = Thread(target=self.gen_action, args=(2, p2_q, queue_out))
        p2.start()

        while True:
            data, player_id = queue_in.get()
            if player_id == 1:
                p1_q.put(data)
            else:
                p2_q.put(data)
