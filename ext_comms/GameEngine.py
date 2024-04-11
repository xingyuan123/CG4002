from game.GameState import GameState
from queue import Queue
from Helper import Status, ice_print_g as print, ice_print_x as alert

class GameEngine:
    """
    Class that will keep track of the game state and evaluate all actions.
    Modified from eval server's GameSimulator.py. 
    """
    def __init__(self, num_players):
        self.game_state     = GameState()
        self.num_players    = num_players

    def perform_action(self, status: Status, action_in: Queue, viz_out: Queue, data_out: Queue, eval_q=None):
        """use the user sent action to alter the game state"""
        players = status.players
        while True:
            can_see = True
            # get action and calculate new game state
            action, player_id = action_in.get()
            print(f'Processing {action} by player {player_id}')
            player = players[player_id]
            player.action_done.set()
            if action == 'gun':
                opponent = players[2] if player_id == 1 else players[1]
                shot = opponent.is_shot.wait(timeout=0.5) 
                if shot:
                    opponent.is_shot.clear()
                else:
                    alert("opponent not shot")
                    can_see = False 
            self.game_state.perform_action(action, player_id, can_see)
            game_state = self.get_game_state_dict()

            # send game state to hardware
            data_out.put(game_state)
            # send player info to eval server
            if not status.freeplay:
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
            if is_different:
                data_out.put(game_state)
                viz_out.put(['game_state', game_state])

    def get_game_state_dict(self):
        return self.game_state.get_dict()
    