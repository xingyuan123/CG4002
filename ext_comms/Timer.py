from threading import Event
from queue import Queue
from Helper import Player, ice_print_t as print
from typing import Dict

failsafe_ai = 'hulk'
failsafe_gun = 'gun'

class Timer:
    def __init__(self, num_players):
        self.num_players = num_players

    def start_timer(self, round_end: Event, disconnect: Event, connect, status: Dict[int, Player], eng_in: Queue):
        failsafe = 45 # time before random ai action is generated
        timeout  = 60 # timeout for eval server = 60s
        while True:
            # DISCONNECT ROUND
            if disconnect.is_set():
                round_end.wait()
                continue
            
            # FAILSAFE
            ended = round_end.wait(timeout=failsafe)
            if ended:
                continue
            # send failsafe if player has not done action yet
            for player in status.values():
                if not player.action_done.is_set():
                    player_id = player.player_id
                    gun_connected = connect[player_id*3].is_set()
                    failsafe_action = failsafe_ai if gun_connected else failsafe_gun
                    print(f'Failsafe: Sending {failsafe_action} for Player {player_id}')
                    eng_in.put([failsafe_action, player_id])

            # TIMEOUT
            ended = round_end.wait(timeout=timeout-failsafe)
            if not ended:
                # timeout, continue w existing gamestate
                print('Timeout')
                round_end.set()
