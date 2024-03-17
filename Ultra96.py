import asyncio
import shutil
from threading import Thread, Event
from queue import Queue
from DataServer import DataServer
from EvalClient import EvalClient
from GameEngine import GameEngine
# from VizMqttClient import VizMqttClient
from Helper import MsgHelper
from time import perf_counter

from dummy_AI import Dummy_AI

w, _ = shutil.get_terminal_size()
def print_line():
    print('='*w)
    
async def main():
    # port = int(input('port: '))
    port = 8888
    password    = '1234567890123456'
    num_players = 1 

    action_done = [Event(), Event()]
    round_end = Event()
    game_end  = Event()

    msg_helper  = MsgHelper(password)

    # Game Engine
    engine = GameEngine(num_players, does_not_have_visualizer=True)
    eng_in = Queue()
    eval_in = Queue()

    # Dummy AI
    dummy_AI = Dummy_AI()

    # Eval Client
    eval_client = EvalClient(msg_helper, port)
    eval_out = Queue()

    # Visualiser
    # viz_client = VizMqttClient()
    viz_out = Queue()

    # Data Server
    data_server = DataServer(msg_helper)
    data_in  = Queue()
    data_out = Queue()
    await data_server.accept()
    
    # 1. TCP: Receive data from data client
    data_recv = Thread(target=data_server.recv_data_p, args=(action_done, data_in, eng_in,))
    data_recv.start()
    
    # 2. AI generate action using data (dummy)
    ai_action = Thread(target=dummy_AI.gen_action, args=(data_in, eng_in, game_end,))
    ai_action.start()

    # 3. Perform action: Updates game state, send to hardware & viz, eval server
    eng_action = Thread(target=engine.perform_action, args=(eng_in, action_done, eval_out, viz_out, data_out,)) 
    eng_action.start()

    # 4. MQTT: Send to Visualiser
    # viz_send = Thread(target=viz_client.send_to_broker, args=(viz_out,))
    # viz_send.start()

    # 5. TCP: Send/receive from Eval Server
    eval_conn = Thread(target=eval_client.conn_eval_server, args=(eval_out, eval_in, round_end,))
    eval_conn.start()

    # 6. Fix game state (if needed): Send to hardware and viz
    eng_fix = Thread(target=engine.fix_game_state, args=(eval_in, viz_out, data_out,))
    eng_fix.start()

    # 7. TCP: Send data back to data client
    data_send = Thread(target=data_server.send_data, args=(data_out,))
    data_send.start()

    queues  = [eng_in, eval_in, viz_out, data_in] # eval_out, data_out not affected by purge
    threads = [data_recv, ai_action, eng_action, eval_conn, eng_fix, data_send] # viz_send, 

    print_line()

    min_rounds = 22
    max_rounds = 23
    num_rounds = 0
    timeout = 70 # timeout for eval server = 60s + buffer
    start_time = perf_counter()
    while True:
        time = perf_counter() - start_time
        if time > timeout:
            round_end.set()
            print('Timeout')
        # at end of every round
        if round_end.is_set():                
            num_rounds += 1
            print(f'Time elapsed for round: {time}')
            print(f'Number of rounds: {num_rounds}\n')

            # clear all queues to prep for next round
            for queue in queues:
                with queue.mutex:
                    queue.queue.clear()
            
            # clear player actions done
            for player in action_done:
                player.clear()
            
            # start next round
            print_line()
            round_end.clear()
            start_time = perf_counter()

        # if logout is possible
        if num_rounds >= min_rounds:
            game_end.set()
        # if game has ended
        if num_rounds >= max_rounds:
            print('Ending game. Bye!')
            for thread in threads:
                thread.join()

if __name__ == "__main__":
    print('Initialising Ultra96')
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
