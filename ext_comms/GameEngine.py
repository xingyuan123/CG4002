from game.GameState import GameState
from queue import Queue
from Helper import ice_print_g as print

class GameEngine:
    """
    Class that will keep track of the game state and evaluate all actions.
    Modified from eval server's GameSimulator.py. 
    """
    def __init__(self, num_players, does_not_have_visualizer):
        self.game_state     = GameState()
        self.num_players    = num_players
        self.does_not_have_visualizer = does_not_have_visualizer 

    def perform_action(self, action_in: Queue, action_done, is_shot, eval_q: Queue, viz_out: Queue, data_out: Queue):
        """use the user sent action to alter the game state"""
        while True:
            can_see = True
            # get action and calculate new game state
            action, player_id = action_in.get()
            print(f'Processing {action} by player {player_id}')
            action_done[player_id].set()
            if action == 'gun':
                opponent = 2 if player_id == 1 else 1
                success = is_shot[opponent].wait(timeout=1) #!!! decrease timeout
                if not success:
                    can_see = False 
            self.game_state.perform_action(action, player_id, can_see)
            game_state = self.get_game_state_dict()

            # send game state to hardware
            data_out.put(game_state)
            # send player info to eval server
            player_info = {
                'player_id': player_id, 
                'action': action, 
                'game_state': game_state
            }
            eval_q.put(player_info)
            # send both to viz
            viz_player_info = {
                'player_id': player_id, 
                'action': action
            }
            viz_out.put(['player_info', viz_player_info])
            viz_out.put(['game_state', game_state])
            
    def fix_game_state(self, game_state_in: Queue, viz_out: Queue, data_out: Queue):
        while True:
            # receive game state from eval server
            received_game_state = game_state_in.get()
            # if game state is different, fix and update hardware, visualiser
            is_different = self.game_state.fix_difference(received_game_state)
            game_state = self.get_game_state_dict()
            data_out.put(game_state) ## !! outside of is_different check, will send both after action and after eval server response
            viz_out.put(['game_state', game_state])
            # if is_different:
                # data_out.put(game_state)
                # viz_out.put(['game_state', game_state])

    def get_game_state_dict(self):
        return self.game_state.get_dict()
    

class _Move:
    def __init__(self, action_1, position_1, action_2, position_2):
        self.action_1   = action_1
        self.position_1 = position_1
        self.action_2   = action_2
        self.position_2 = position_2

    def __str__(self):
        return "p1:{},{}; p2:{},{}".format(self.position_1, self.action_1, self.position_2, self.action_2)
