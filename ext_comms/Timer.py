from threading import Event
from queue import Queue
from Helper import ice_print_t as print

failsafe_ai = 'hulk'
failsafe_gun = 'gun'

class Timer:
    def __init__(self, num_players):
        self.num_players = num_players

    def start_timer(self, round_end: Event, disconnect: Event, connect, action_done, eng_in: Queue):
        failsafe = 45 # time before random ai action is generated
        timeout  = 60 # timeout for eval server = 60s + 10s buffer
        while True:
            # DISCONNECT ROUND
            if disconnect.is_set():
                round_end.wait()
                continue
            
            # FAILSAFE
            ended = round_end.wait(timeout=failsafe)
            if ended:
                continue
            # send failsafe
            for i in range(self.num_players):
                player_id = i+1
                if not action_done[player_id].is_set():
                    gun_connected = connect[player_id*3].is_set()
                    # print(f'P{player_id} gun is connected: {gun_connected}')
                    failsafe_action = failsafe_ai if gun_connected else failsafe_gun
                    print(f'Failsafe: Sending {failsafe_action} for Player {player_id}')
                    eng_in.put([failsafe_action, player_id])

            # TIMEOUT
            ended = round_end.wait(timeout=timeout-failsafe)
            if not ended:
                # timeout, continue w existing gamestate
                print('Timeout')
                round_end.set()


        # if not connect[0].is_set() and num_rounds >= 17 and num_rounds <= 20: 
        #     # ignore timeout for disconn round
        #     start_time = perf_counter()
        # # send failsafe only if no response from hardware
        # if not failsafe_sent and time > failsafe and ai_done.is_set() and not eval_client.sent.is_set(): # !!!
        #     if not connect[3].is_set():
        #         failsafe_action = 'gun'
        #     else:
        #         failsafe_action = 'hulk'
        #     print(f'Failsafe: Sending {failsafe_action}')
        #     for i in range(num_players):
        #         player_id = i+1
        #         eng_in.put([failsafe_action, player_id])
        #     failsafe_sent = True
        # # server timeout
        # if time > timeout:
        #     round_end.set()
        #     
