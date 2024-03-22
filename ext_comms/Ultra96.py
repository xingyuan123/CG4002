import asyncio
import shutil
from threading import Thread, Event
from queue import Queue
from DataServer import DataServer
from EvalClient import EvalClient
from GameEngine import GameEngine
# from VizMqttClient import VizMqttClient
# from ai.MLP_wrapper import MLP as AI
from dummy_AI import Dummy_AI as AI
from Timer import Timer
from Helper import MsgHelper
from time import perf_counter, sleep

def print_line():
    w, _ = shutil.get_terminal_size()
    print('='*w)
    
async def main():
    port = int(input('port: '))
    # port = 8888
    password    = '1234567890123456'
    num_players = 2

    min_rounds = 21
    max_rounds = 30
    num_rounds = 0

    action_done = {
        1: Event(), 
        2: Event()
    }
    is_shot = {
        1: Event(), 
        2: Event()
    }
    connect = [Event() for _ in range(7)]
    if num_players == 1:
        # unused devices
        for i in [1, 5, 6]:
            connect[i].set()
   
    disconnect = Event()
    round_end  = Event()
    game_end   = Event()
    ai_done    = Event()
    ai_done.set()

    msg_helper  = MsgHelper(password)

    # Game Engine
    engine = GameEngine(num_players, does_not_have_visualizer=True)
    eng_in = Queue()
    eval_in = Queue()

    # AI
    ai = AI()

    # Eval Client
    eval_client = EvalClient(num_players, msg_helper, port)
    eval_out = Queue()

    # # Visualiser
    # viz_client = VizMqttClient()
    viz_out = Queue()

    # Timer
    timer = Timer(num_players)

    # Data Server
    data_server = DataServer(msg_helper)
    data_in  = Queue()
    data_out = Queue()
    await data_server.accept()
    
    # 1. TCP: Receive data from data client
    data_recv  = Thread(target=data_server.recv_data_p, args=(action_done, is_shot, ai_done, connect, data_in, eng_in,))
    
    # 2. AI generate action using data (dummy)
    ai_action  = Thread(target=ai.gen_action, args=(ai_done, data_in, eng_in, game_end,))

    # 3. Perform action: Updates game state, send to hardware & viz, eval server
    eng_action = Thread(target=engine.perform_action, args=(eng_in, action_done, is_shot, eval_out, viz_out, data_out,)) 

    # # 4. MQTT: Send to Visualiser
    # viz_send   = Thread(target=viz_client.send_to_broker, args=(viz_out,))

    # 5. TCP: Send/receive from Eval Server
    eval_conn  = Thread(target=eval_client.conn_eval_server, args=(eval_out, eval_in, round_end,))

    # 6. Fix game state (if needed): Send to hardware and viz
    eng_fix    = Thread(target=engine.fix_game_state, args=(eval_in, viz_out, data_out,))

    # 7. TCP: Send data back to data client
    data_send  = Thread(target=data_server.send_data, args=(data_out,))

    # 8. Timer for failsafe actions, timeout
    timing     = Thread(target=timer.start_timer, args=(round_end, disconnect, connect, action_done, eng_in,))

    queues  = [eng_in, eval_in, data_in, eval_out] # viz_out, data_out
    threads = [ai_action, eng_action, eval_conn, eng_fix, data_send, timing] # viz_send, 

    # receive initial connect packets
    data_recv.start()
    connect[0].wait()

    # initialise
    for queue in queues:
        with queue.mutex:
            queue.queue.clear()
    for thread in threads: 
        thread.start()
    print('Starting game')
    print_line()
    while True:
        # at end of every round
        round_end.wait()
        num_rounds += 1
        print(f'Number of rounds: {num_rounds}')

        # clear queues to prep for next round
        for queue in queues:
            with queue.mutex:
                queue.queue.clear()
        
        # clear player done & shot status after delay
        sleep(2)
        for player in range(1, num_players+1):
            action_done[player].clear()
            is_shot[player].clear()
        eval_client.sent.clear()
        eval_client.received.clear()

        # if disconn is possible
        if num_rounds in range(18, min_rounds):
            disconnect.set()
        else:
            disconnect.clear()
        # if logout is possible
        if num_rounds >= min_rounds:
            game_end.set()
        # if game has ended
        if num_rounds >= max_rounds:
            break

        # start next round
        print_line()
        round_end.clear()

    for thread in threads:
        thread.join()
    print('Ending game. Bye!')

if __name__ == "__main__":
    print('Initialising Ultra96')
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
