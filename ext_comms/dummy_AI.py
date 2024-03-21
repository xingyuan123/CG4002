from queue import Queue
from random import randint
from time import sleep
from threading import Event
from Helper import ice_print_a as print, ice_print_x as alert

# attacks, shield, reload or shoot
actions = ['bomb', 'captAmerica', 'hulk', 'idle', 'ironMan', 'logout', 'reload', 'shangChi', 'shield']

class Dummy_AI: 
    def gen_action(self, done: Event, queue_in: Queue, queue_out: Queue, end: Event):
        print('AI running')
        while True:
            data, player_id = queue_in.get()
            done.clear()
            print(f'Got {data}')
            sleep(3) # temp
            action = actions[randint(0, 8)]
            action = 'bomb'
            print(f'Generate {action} by player {player_id}')

            # handle idle action
            if action == 'idle':
                alert('Idle received. Try again')
            # stop early logout
            elif action == 'logout' and not end.is_set():
                alert('Logout received early. Try again')
            else:
                queue_out.put([action, player_id])
            done.set()
            