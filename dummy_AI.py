from queue import Queue
from random import randint
from time import sleep
from threading import Event
from Helper import ice_print_a as print

# attacks, shield, reload or shoot
actions = ['bomb', 'ironMan', 'hulk', 'captAmerica', 'shangChi', 'shield', 'reload', 'logout']

class Dummy_AI: 
    def gen_action(self, queue_in: Queue, queue_out: Queue, end: Event):
        print('AI running')
        while True:
            data, player_id = queue_in.get()
            print(f'Got {data}')
            action = actions[randint(0, 7)]
            action = 'bomb'
            print(f'Generate {action} by player {player_id}')

            # stop early logout, get another action
            if action == 'logout' and not end.is_set():
                print(f'Logout received early. Try again')
                continue
            
            queue_out.put([action, player_id])
            sleep(1) # temp measure to prevent 
