from queue import Queue
from Helper import Status, ice_print_t as print

failsafe_ai = 'hulk'
failsafe_gun = 'gun'

class Timer:
    def __init__(self, num_players):
        self.num_players = num_players

    def start_timer(self, status: Status, eng_in: Queue):
        round_end  = status.round_end
        disconnect = status.disconnect
        connect    = status.connect
        players    = status.players

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
            for player in players.values():
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
                status.inc_rounds()
