import asyncio
import shutil
from threading import Thread
from queue import Queue
from DataServer import DataServer
from EvalClient import EvalClient
from GameEngine import GameEngine
from VizMqttClient import VizMqttClient
from ai.MLP_wrapper import MLP as AI
from Timer import Timer
from Helper import MsgHelper, Status
from time import sleep

def print_line():
    w, _ = shutil.get_terminal_size()
    print('='*w)
    
async def main():
    password    = '1234567890123456'
    num_players = 2

    status      = Status(num_players)
    msg_helper  = MsgHelper(password)

    # Game Engine
    engine = GameEngine(num_players)
    eng_in = Queue()
    eval_in = Queue()

    # AI
    ai = AI()

    # Eval Client
    eval_client = EvalClient(num_players, msg_helper)
    eval_out = Queue()

    # Visualiser
    viz_client = VizMqttClient()
    viz_out = Queue()

    # Timer
    timer = Timer(num_players)

    # Data Server
    data_server = DataServer(msg_helper)
    data_in  = Queue()
    data_out = Queue()
    await data_server.accept()
    
    # 1. TCP: Receive data from data client
    data_recv  = Thread(target=data_server.recv_data_p, args=(status, data_in, eng_in, viz_out,))
    data_recv.daemon = True
    
    # 2. AI generate action using data (dummy)
    ai_action  = Thread(target=ai.run_ai, args=(status, data_in, eng_in,))

    # 3. Perform action: Updates game state, send to hardware & viz, eval server
    eng_action = Thread(target=engine.perform_action, args=(status, eng_in, viz_out, data_out, eval_out,)) 

    # 4. MQTT: Send to Visualiser
    viz_send   = Thread(target=viz_client.send_to_broker, args=(viz_out,))

    # 5. TCP: Send/receive from Eval Server
    eval_conn  = Thread(target=eval_client.conn_eval_server, args=(eval_out, eval_in, status,))

    # 6. Fix game state (if needed): Send to hardware and viz
    eng_fix    = Thread(target=engine.fix_game_state, args=(eval_in, viz_out, data_out,))

    # 7. TCP: Send data back to data client
    data_send  = Thread(target=data_server.send_data, args=(data_out,))

    # 8. Timer for failsafe actions, timeout
    timing     = Thread(target=timer.start_timer, args=(status, eng_in,))

    queues  = [eng_in, eval_in, data_in, eval_out] 
    threads = [ai_action, eng_action, eval_conn, eng_fix, data_send, timing, viz_send]

    # receive initial connect packets
    data_recv.start()
    status.connect[0].wait()

    # connect to eval server
    eval_client.start()
    # clear queues
    for queue in queues:
        with queue.mutex:
            queue.queue.clear()
    # start threads
    for thread in threads: 
        thread.daemon = True
        thread.start()

    print('Starting game')
    print_line()
    while True:
        # at end of every round
        status.round_end.wait()
        eval_client.received.set()
        print(f'Number of rounds: {status.num_rounds}')

        # clear queues to prep for next round
        for queue in queues:
            with queue.mutex:
                queue.queue.clear()
        
        # clear player done & shot status after delay
        sleep(2)
        for player in status.players.values():
            player.action_done.clear()
        eval_client.sent.clear()
        eval_client.received.clear()

        # if game has ended
        if status.num_rounds >= status.max_rounds:
            break

        # start next round
        print_line()
        status.round_end.clear()

    for thread in threads:
        thread.join()
    print('Ending game. Bye!')

if __name__ == "__main__":
    print('Initialising Ultra96')
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
